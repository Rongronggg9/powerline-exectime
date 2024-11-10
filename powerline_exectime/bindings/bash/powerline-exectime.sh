# Detect if the bash binding of powerline is already sourced.
if [ "$(type -t _powerline_status_wrapper)" != "function" ]; then
	echo "Please source the bash binding of powerline before powerline-exectime"
	return
fi

if [ -n "$EPOCHREALTIME" ]; then  # Bash 5+
  # Produce microseconds.
  # Only integer is valid in arithmetic expressions, so '.' (or ',' in some locales) must be removed.
  PS0='\[${PS1:$((_POWERLINE_EXECTIME_TIMER_START="${EPOCHREALTIME/[^0-9]/}")):0}\]'
  _powerline_exectime_at_stop() {
    _POWERLINE_EXECTIME_TIMER_STOP="${EPOCHREALTIME/[^0-9]/}"
  }
else
  # Produce nanoseconds.
  PS0='\[${PS1:$((_POWERLINE_EXECTIME_TIMER_START="$(date +%s%N)")):0}\]'
  _powerline_exectime_at_stop() {
    read -rs _POWERLINE_EXECTIME_TIMER_STOP < <(date +%s%N)
  }
fi

# Override the vanilla powerline function.
_powerline_status_wrapper() {
	# Copied from powerline/bindings/bash/powerline.sh and modified.
	local last_exit_code="$?" last_pipe_status=( "${PIPESTATUS[@]}" )
  _powerline_exectime_at_stop

	if ! _powerline_has_pipestatus \
	   || test "${#last_pipe_status[@]}" -eq "0" \
	   || test "$last_exit_code" != "${last_pipe_status[$(( ${#last_pipe_status[@]} - 1 ))]}" ; then
		last_pipe_status=()
	fi

	if [ -n "$_POWERLINE_EXECTIME_TIMER_START" ]; then
    local extra_args=(
      "--renderer-arg=exec_start=$_POWERLINE_EXECTIME_TIMER_START"
      "--renderer-arg=exec_end=$_POWERLINE_EXECTIME_TIMER_STOP"
    )
		POWERLINE_COMMAND_ARGS="$POWERLINE_COMMAND_ARGS ${extra_args[*]}" "$@" $last_exit_code "${last_pipe_status[*]}"
	else
    # Skip the timer if it's not set (e.g. pressing enter without typing a command).
		"$@" $last_exit_code "${last_pipe_status[*]}"
	fi

  unset _POWERLINE_EXECTIME_TIMER_START _POWERLINE_EXECTIME_TIMER_STOP
	return $last_exit_code
}
