# vim:fileencoding=utf-8:noet
import re
from math import log10, ceil
from time import time

from powerline.theme import requires_segment_info

MILLISECONDS = 10.0 ** 3  # ms
HIGHLIGHT_GROUPS = ['exectime_gradient', 'system_load_gradient', 'network_load_gradient', 'system_load']

# https://github.com/bminor/bash/blob/fa68e6da80970c302948674369d278164a33ed39/lib/sh/clock.c#L78
# "%ldm%d%c%03lds": "0m0.099s", "0m0,099s".
# %ld:minutes, %d:seconds, %c:locale_decpoint(), %03ld:seconds_fraction
BASH_TIMES_COMPONENT_REGEX = re.compile(r'(\d+)m(\d+)[.,](\d+)s', re.IGNORECASE)


def guess_ts_multiplier(ts):
    approx_multiplier = ts / time()
    exponent = ceil(log10(approx_multiplier))
    return 10 ** -exponent


def parse_times_component(times_component):
    match = BASH_TIMES_COMPONENT_REGEX.fullmatch(times_component)
    if match is None:
        return None
    minutes, seconds, seconds_fraction = match.groups()
    return float(minutes) * 60.0 + float(seconds) + float(seconds_fraction) * 0.001


def parse_times(times):
    if times is None:
        return None, None
    times_components = times.split(';')
    if len(times_components) != 4:
        return None, None
    shell_user, shell_sys, child_user, child_sys = map(parse_times_component, times_components)
    user_time = (
        None
        if shell_user is None or child_user is None
        else shell_user + child_user
    )
    sys_time = (
        None
        if shell_sys is None or child_sys is None
        else shell_sys + child_sys
    )
    return user_time, sys_time


class _Exectime:
    def __init__(
            self,
            threshold,
            significant_figures,
            max_parts,
            gradient_range_low,
            gradient_range_high,
            highlight_groups,
    ):
        self.threshold = threshold
        self.significant_figures = significant_figures
        self.max_parts = max_parts
        self.gradient_range_low = gradient_range_low
        self.gradient_range_high = gradient_range_high

        if highlight_groups is None:
            self.highlight_groups = HIGHLIGHT_GROUPS
        elif not isinstance(highlight_groups, list):
            self.highlight_groups = [highlight_groups] + HIGHLIGHT_GROUPS
        else:
            self.highlight_groups = highlight_groups + HIGHLIGHT_GROUPS

    def _fmt_significant(self, fl):
        return '{:g}'.format(float('{:.{p}g}'.format(fl, p=self.significant_figures)))

    def _fmt_time(self, ts):
        if ts <= 10:
            return self._fmt_significant(ts * MILLISECONDS) + 'ms'
        else:
            _, dot, frac = self._fmt_significant(ts).partition('.')
            seconds = int(ts)
            minutes = seconds // 60
            seconds %= 60
            hours = minutes // 60
            minutes %= 60
            days = hours // 24
            hours %= 24
            buf = []
            parts = 0
            max_parts = self.max_parts
            if days and parts < max_parts:
                buf.extend((str(days), 'd '))
                parts += 1
            if hours and parts < max_parts:
                buf.extend((str(hours), 'h'))
                parts += 1
            if minutes and parts < max_parts:
                buf.extend((str(minutes), 'm'))
                parts += 1
            if parts < max_parts:
                buf.extend((str(seconds), dot, frac, 's'))
            return ''.join(buf).strip()

    def _calc_gradient_level(self, ts):
        gradient_level = (ts - self.gradient_range_low) / (self.gradient_range_high - self.gradient_range_low) * 100.0
        return max(min(gradient_level, 100), 0)

    def _from_ts_diff(self, ts_diff, _prefix=''):
        if ts_diff <= self.threshold:
            return []
        return [{
            'contents': _prefix + self._fmt_time(ts_diff),
            'highlight_groups': self.highlight_groups,
            'gradient_level': self._calc_gradient_level(ts_diff),
            'draw_inner_divider': True,
        }]

    def wall_time(self, start, end, _prefix=''):
        if start is None or end is None:
            return []
        start, end = float(start), float(end)
        return self._from_ts_diff((end - start) * guess_ts_multiplier(end))

    def user_sys_time(self, times_prev, times, _user_time_prefix='', _sys_time_prefix=''):
        segments = []
        user_time_prev, sys_time_prev = parse_times(times_prev)
        user_time, sys_time = parse_times(times)
        if user_time_prev is not None and user_time is not None:
            segments.extend(self._from_ts_diff(user_time - user_time_prev, _prefix=_user_time_prefix))
        if sys_time_prev is not None and sys_time is not None:
            segments.extend(self._from_ts_diff(sys_time - sys_time_prev, _prefix=_sys_time_prefix))
        return segments


@requires_segment_info
def exectime(
        pl,
        segment_info,
        threshold=0.0,
        significant_figures=3,
        max_parts=2,
        gradient_range_low=0.5,
        gradient_range_high=30.0,
        highlight_groups=None,
        wall_time_prefix='',
        user_time_prefix='u:',
        sys_time_prefix='s:',
        enable_user_sys_time=False,
):
    """
    Return the execution time of the last command.

    :param float threshold:
        The minimum execution time in seconds to display the execution time.
    :param int significant_figures:
        The number of significant figures to display in the execution time.
    :param int max_parts:
        The maximum number of parts to display in the execution time. E.g., if
        the execution time is 1d2h3m4s and max_parts=2, then it will be displayed
        as 1d2h.
    :param float gradient_range_low:
        If the execution time is less than or equal to this value, then the
        gradient level will be 0%.
    :param float gradient_range_high:
        If the execution time is greater than or equal to this value, then the
        gradient level will be 100%.
    :param list highlight_groups:
        Override the default highlight groups.
    :param str wall_time_prefix:
        The prefix of the wall time segment.
    :param str user_time_prefix:
        The prefix of the user time segment.
    :param str sys_time_prefix:
        The prefix of the system time segment.
    :param bool enable_user_sys_time:
        Enable the user time and system time segments.
    """
    ex = _Exectime(threshold, significant_figures, max_parts, gradient_range_low, gradient_range_high, highlight_groups)

    segments = []

    start = segment_info.get('exec_start')
    end = segment_info.get('exec_end')
    segments.extend(ex.wall_time(start, end, _prefix=wall_time_prefix))

    if not enable_user_sys_time:
        return segments

    times_prev = segment_info.get('exec_times_prev')
    times = segment_info.get('exec_times')
    segments.extend(
        ex.user_sys_time(times_prev, times, _user_time_prefix=user_time_prefix, _sys_time_prefix=sys_time_prefix)
    )

    return segments
