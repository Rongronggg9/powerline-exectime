# vim:fileencoding=utf-8:noet

from powerline.theme import requires_segment_info

MILLISECONDS = 1000
NANOSECONDS = 1000000000
HIGHLIGHT_GROUPS = ['exectime_gradient', 'system_load_gradient', 'network_load_gradient', 'system_load']


def fmt_significant(f, significant_figures):
    return '{:g}'.format(float('{:.{p}g}'.format(f, p=significant_figures)))


def fmt_time(t, significant_figures, max_parts):
    if t < 10:
        t *= MILLISECONDS
        return fmt_significant(t, significant_figures) + 'ms'
    else:
        buf = ''
        parts = 0
        t_sig = fmt_significant(t, significant_figures).split('.')
        t = int(t_sig[0])
        frac = t_sig[1] if len(t_sig) > 1 else ''
        seconds = t % 60
        minutes = t // 60
        hours = minutes // 60
        minutes %= 60
        days = hours // 24
        hours %= 24
        if days and parts < max_parts:
            buf += str(days) + 'd '
            parts += 1
        if hours and parts < max_parts:
            buf += str(hours) + 'h'
            parts += 1
        if minutes and parts < max_parts:
            buf += str(minutes) + 'm'
            parts += 1
        if parts < max_parts:
            if seconds and frac:
                buf += str(seconds) + '.' + frac + 's'
            elif seconds:
                buf += str(seconds) + 's'
            elif frac:
                buf += '0.' + frac + 's'
        return buf.strip()


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
    """
    if highlight_groups is None:
        highlight_groups = []
    elif not isinstance(highlight_groups, list):
        highlight_groups = [highlight_groups]
    try:
        end, start = segment_info['exec_end'], segment_info['exec_start']
    except KeyError:
        return None
    t = (float(end) - float(start)) / NANOSECONDS
    if t <= threshold:
        return None
    gradient_level = (t - gradient_range_low) / (gradient_range_high - gradient_range_low) * 100
    return [{
        'contents': fmt_time(t, significant_figures, max_parts),
        'highlight_groups': highlight_groups + HIGHLIGHT_GROUPS,
        'gradient_level': max(min(gradient_level, 100), 0)
    }]
