# Detect if the bash binding of powerline is already sourced.
if [ "$(type -t _powerline_status_wrapper)" != "function" ]; then
	echo "Please source the bash binding of powerline before powerline-exectime"
	return 1
fi

# Create an FIFO used to capture the output of `times`.
_POWERLINE_EXECTIME_TIMES_F="${TMPDIR:-/tmp}/powerline-exectime.$RANDOM.$RANDOM"
mkfifo "$_POWERLINE_EXECTIME_TIMES_F" || return 1
exec {_POWERLINE_EXECTIME_TIMES_FD}<>"$_POWERLINE_EXECTIME_TIMES_F"
unlink "$_POWERLINE_EXECTIME_TIMES_F"
unset _POWERLINE_EXECTIME_TIMES_F

# Measure startup time by setting a dummy default value.
_POWERLINE_EXECTIME_TIMES="${_POWERLINE_EXECTIME_TIMES:-0m0.000s;0m0.000s;0m0.000s;0m0.000s}"

# `times` is reset in a subshell. Execute it in the current shell by utilizing the FIFO.
_powerline_exectime_capture_times() {
	times >&"$_POWERLINE_EXECTIME_TIMES_FD"
	local shell_user shell_sys child_user child_sys
	read -rst 1 shell_user shell_sys <&"$_POWERLINE_EXECTIME_TIMES_FD"
	read -rst 1 child_user child_sys <&"$_POWERLINE_EXECTIME_TIMES_FD"
	_POWERLINE_EXECTIME_TIMES_PREV="$_POWERLINE_EXECTIME_TIMES"
	_POWERLINE_EXECTIME_TIMES="$shell_user;$shell_sys;$child_user;$child_sys"
}

if [ -n "$EPOCHREALTIME" ]; then  # Bash 5+
	# Produce microseconds.
	# Only integer is valid in arithmetic expressions, so '.' (or ',' in some locales) must be removed.
	PS0='\[${PS1:$((_POWERLINE_EXECTIME_TIMER_START="${EPOCHREALTIME/[^0-9]/}")):0}\]'
	_powerline_exectime_at_stop() {
		_POWERLINE_EXECTIME_TIMER_END="${EPOCHREALTIME/[^0-9]/}"
	}
else
	# Produce nanoseconds.
	PS0='\[${PS1:$((_POWERLINE_EXECTIME_TIMER_START="$(date +%s%N)")):0}\]'
	_powerline_exectime_at_stop() {
		read -rs _POWERLINE_EXECTIME_TIMER_END < <(date +%s%N)
	}
fi

# Override the vanilla powerline function.
# Copied from powerline/bindings/bash/powerline.sh and modified.
_powerline_status_wrapper() {
	local last_exit_code="$?" last_pipe_status=( "${PIPESTATUS[@]}" )

	# Capture user time and system time (overhead: 0.x ms).
	_powerline_exectime_capture_times
	# Capture wall time (overhead: 0.x ms on Bash 5+, 1~10ms on Bash 4).
	_powerline_exectime_at_stop

	if ! _powerline_has_pipestatus \
		 || test "${#last_pipe_status[@]}" -eq "0" \
		 || test "$last_exit_code" != "${last_pipe_status[$(( ${#last_pipe_status[@]} - 1 ))]}" ; then
		last_pipe_status=()
	fi

	if [ -n "$_POWERLINE_EXECTIME_TIMER_START" ]; then
		local extra_args=(
			"--renderer-arg=exec_start=$_POWERLINE_EXECTIME_TIMER_START"
			"--renderer-arg=exec_end=$_POWERLINE_EXECTIME_TIMER_END"
			"--renderer-arg=exec_times_prev=\"$_POWERLINE_EXECTIME_TIMES_PREV\""
			"--renderer-arg=exec_times=\"$_POWERLINE_EXECTIME_TIMES\""
		)
		POWERLINE_COMMAND_ARGS="$POWERLINE_COMMAND_ARGS ${extra_args[*]}" "$@" $last_exit_code "${last_pipe_status[*]}"
	else
		# Skip the timer if it's not set (e.g. pressing enter without typing a command).
		"$@" $last_exit_code "${last_pipe_status[*]}"
	fi

	# Update user time and system time to prevent the overhead of prompting from being calculated.
	_powerline_exectime_capture_times
	unset _POWERLINE_EXECTIME_TIMER_START _POWERLINE_EXECTIME_TIMER_END
	return $last_exit_code
}
