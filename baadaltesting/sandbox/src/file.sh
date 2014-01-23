function file_copy
{
  source=$1
  destination=$2

  $ECHO_PROGRESS "$source -\> $destination"
  cp $source $destination 1>>$LOGS/log.out 2>>$LOGS/log.err
  status=$?

  if [[ $status -ne 0 ]]; then
    $ECHO_ER Copying $source to $destination failed. Check logs.
    exit 1
  else
    $ECHO_OK $source -\> $destination
  fi
}

function file_backup
{
  file=$1

  $ECHO_PROGRESS "$file -\> $file.bak"

  mv $file $file.bak 1>>$LOGS/log.out 2>>$LOGS.log.err

  $ECHO_OK $file -\> $file.bak
}
