#!/usr/bin/env python

import random
import re
import subprocess
import sys
import tempfile

find_dbg_value = re.compile('call void @llvm.dbg.value')

def size_to_delete_lines(n, cur_factor):
  if n < 30:
    return 1
  res = n / cur_factor 
  return res if res != 0 else 1
  

def rand_disable(n, theset, R):
  newset = theset.copy()
  for x in range(n):
    todelete = R.randint(0, len(newset) - 1)
    theitem = list(enumerate(newset))[todelete]
    idx, item = theitem
    newset.remove(item)
  return newset

def filter_output(f, lines, enabled_dbg_values, dbg_value_index):
  for idx, line in enumerate(lines):
    if not dbg_value_index[idx]:
      f.write(line)
    elif idx in enabled_dbg_values:
      f.write(line)
    # otherrwise skip

def gen_filtered_file(lines, enabled, index):
  f = tempfile.NamedTemporaryFile(suffix=".ll")
  filter_output(f, lines, enabled, index)
  return f

if __name__ == '__main__':
  R = random.Random()
  inpfile = sys.argv[1]
  varname = sys.argv[2]
  outfile = sys.argv[3]
  with open(outfile, "w") as f:
    pass # ensure it's writable

  with open(inpfile, "r") as f:
    the_lines = f.readlines()

  isdbgvalue = lambda x: 'call void @llvm.dbg.value' in x
  dbg_value_index = {idx: isdbgvalue(line) for idx, line in enumerate(the_lines)}
  enabled = {idx for idx, isdbgvalue in dbg_value_index.items() if isdbgvalue}

  # Go through and delta these things. Remove n random lines according to the
  # size still available:

  new_enabled = enabled.copy()
  main_factor = 4
  cur_factor = 4
  time_since_last_failure = 0
  while len(new_enabled) > 30:
    num_to_disable = size_to_delete_lines(len(new_enabled), cur_factor)
    print("Disabling {}".format(num_to_disable))
    test_enabled = rand_disable(num_to_disable, new_enabled, R)
    testfile = gen_filtered_file(the_lines, test_enabled, dbg_value_index)

    testfile.flush()
    res = subprocess.call(['./hasdumpvardiff.sh', varname, testfile.name])
    testfile.close()

    if res == 0:
      new_enabled = test_enabled
      print("filtered down to {}".format(len(new_enabled)))
      time_since_last_failure = 0
      cur_factor = main_factor
    else:
      print("1x failure")
      time_since_last_failure += 1
      cur_factor = main_factor * time_since_last_failure

  # When we have less than 30: just linearly disable them, until we've tested
  # them all. I've never seen any more complex than that.

  to_remain = set()
  count = len(new_enabled)
  for num, x in enumerate(new_enabled):
    print("testing {} of {}".format(num, count))
    tmp_enabled = new_enabled.copy()
    tmp_enabled.remove(x)
    testfile = gen_filtered_file(the_lines, tmp_enabled, dbg_value_index)

    testfile.flush()
    res = subprocess.call(['./hasdumpvardiff.sh', varname, testfile.name])
    testfile.close()

    if res == 0:
      # We still interesting without this one; continue on.
      pass
    else:
      # We were not interesting; this is necessary.
      to_remain.add(x)

  # Produce final file:
  with open(outfile, "w") as f:
    filter_output(f, the_lines, to_remain, dbg_value_index)
