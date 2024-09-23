# detect if the bash binding of powerline is already sourced
if [ "$(type -t _powerline_status_wrapper)" != "function" ]; then
	echo "Please source the bash binding of powerline before powerline-exectime"
	return
fi

# only integer is valid in arithmetic expressions, so '.' (or ',' in some locales) must be removed
# removing '.' is equivalent to EPOCHREALTIME*10^6
PS0='\[${PS1:$((_POWERLINE_EXECTIME_TIMER_START="${EPOCHREALTIME/[^0-9]/}")):0}\]'

# override the vanilla powerline function
_powerline_status_wrapper() {
	# copied from powerline/bindings/bash/powerline.sh and modified
	local last_exit_code="$?" last_pipe_status=( "${PIPESTATUS[@]}" ) timer_end="${EPOCHREALTIME/[^0-9]/}"

	if ! _powerline_has_pipestatus \
	   || test "${#last_pipe_status[@]}" -eq "0" \
	   || test "$last_exit_code" != "${last_pipe_status[$(( ${#last_pipe_status[@]} - 1 ))]}" ; then
		last_pipe_status=()
	fi
	if [ -n "$_POWERLINE_EXECTIME_TIMER_START" ]; then
		local extra_args="--renderer-arg=exec_end=$timer_end --renderer-arg=exec_start=$_POWERLINE_EXECTIME_TIMER_START"
		unset _POWERLINE_EXECTIME_TIMER_START
		POWERLINE_COMMAND_ARGS="$POWERLINE_COMMAND_ARGS $extra_args" "$@" $last_exit_code "${last_pipe_status[*]}"
	else
		# skip the timer if it's not set (e.g. pressing enter without typing a command)
		"$@" $last_exit_code "${last_pipe_status[*]}"
	fi
	return $last_exit_code
}
