
#! /bin/bash 
 
set -u
set -o pipefail

W_TOOL_ABS_NAME="WRAPPER_TEMPLATE_RUN_EXE_ASBSOLUTE_PATH"
W_COUNTER_FILE="WRAPPER_TEMPLATE_COUNTER_FILE"
W_OUTPUT_RETCODE="WRAPPER_TEMPLATE_OUTPUT_RETCODE"
W_OUTPUT_LOG="WRAPPER_TEMPLATE_OUTPUT_LOG"

W_EXEC_TIMEOUT=""
if [ "${MUTERIA_TEST_EXECUTION_TIMEOUT_ENV_VAR:-}" != "" ]; then
    W_EXEC_TIMEOUT="$MUTERIA_TEST_EXECUTION_TIMEOUT_ENV_VAR"
fi

plain_replay() {
    if [ "$W_EXEC_TIMEOUT" != "" ]; then
        exec /usr/bin/timeout -s 9 $W_EXEC_TIMEOUT $W_TOOL_ABS_NAME "${@:1}"
    else
        exec $W_TOOL_ABS_NAME "${@:1}"
    fi
}

if [ "${MUTERIA_TEST_FILE_NAME_ENV_VAR:-}" = "" ]; then 
    plain_replay
else
    # Check test file match
    if ! `/bin/ps $$ | /bin/grep "$MUTERIA_TEST_FILE_NAME_ENV_VAR "` ; then
        plain_replay
    fi
fi

if [ "${MUTERIA_TEST_COUNT_ID_ENV_VAR:-}" != "" ]; then
# critical section
  # FD is redirected to our lock file
  FD=200
  eval "exec ${FD}>$W_COUNTER_FILE.lock"

  # try to lock the file with timeout of 1s
  /usr/bin/flock -w 60 $FD
  [ $? -eq 1 ] && /bin/echo "failed to aquire the lock" >> /tmp/mylog

  # set a default value that will prevent from executing klee-replay
  COUNTER=0
  
  # check if the argv that the wrapper was called with is the desired argv
  #if [[ "$EKLEEPSE_REPLAY_MODE" = 0 || "$argv" = "$EKLEEPSE_REPLAY_ARGV" ]]
  #then
    # the current argv is the desired one; now we need to get the value of the
    # counter from the file; the counter establishes an order in case of multiple
    # occurrences of the same argv     

    # first, we need to get the value of the counter from a file
    /usr/bin/test -f "$W_COUNTER_FILE" || /bin/echo "$COUNTER" > "$W_COUNTER_FILE"
    COUNTER=`/bin/cat "$W_COUNTER_FILE"`
    # echo "COUNTER = $COUNTER"

    # decrement the counter and store it in the file
    CNT=$((COUNTER + 1))
    /bin/echo "$CNT" > "$W_COUNTER_FILE"
  #fi

  # release the lock
  /usr/bin/flock -u $FD
# end of critical section 
else
    COUNTER=""
    MUTERIA_TEST_COUNT_ID_ENV_VAR="$COUNTER"
fi

if [ "$COUNTER" = "$MUTERIA_TEST_COUNT_ID_ENV_VAR" ]; then
    /bin/echo "TOOL: $(/usr/bin/basename $W_TOOL_ABS_NAME)" > "$W_OUTPUT_LOG"
    if [ "$W_EXEC_TIMEOUT" != "" ]; then
        /usr/bin/timeout -s 9 $W_EXEC_TIMEOUT $W_TOOL_ABS_NAME "${@:1}" 2>&1 | /usr/bin/tee -a "$W_OUTPUT_LOG"
        retcode="$?"
        /bin/echo "$retcode" >> "$W_OUTPUT_RETCODE" 
    else
        $W_TOOL_ABS_NAME "${@:1}" 2>&1 | /usr/bin/tee -a "$W_OUTPUT_LOG"
        retcode="$?"
        /bin/echo "$retcode" >> "$W_OUTPUT_RETCODE" 
    fi

    exit $retcode
else
    plain_replay
fi