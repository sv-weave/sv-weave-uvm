// Self-check helpers for sv-weave sim testbenches.
//
// Convention: a testbench calls check_pkg::pass() once at the end, which prints
// "SV_WEAVE_TEST: PASS". Any failed check calls $fatal with "SV_WEAVE_TEST: FAIL".
`ifndef SV_WEAVE_CHECK_PKG_SV
`define SV_WEAVE_CHECK_PKG_SV

`define CHECK(cond, msg) \
  if (!(cond)) check_pkg::fail($sformatf("%s:%0d: %s", `__FILE__, `__LINE__, msg));

`define CHECK_EQ(actual, expected, msg) \
  if ((actual) != (expected)) check_pkg::fail($sformatf("%s:%0d: %s: got %0p, expected %0p", \
      `__FILE__, `__LINE__, msg, actual, expected));

// UVM: obj is the woven form of class T -- it reports T's type name, but the factory
// created a different (woven) type.
`define CHECK_WOVEN(obj, T, msg) \
  `CHECK_EQ(obj.get_type_name(), T::type_name(), {msg, ": type name"}) \
  `CHECK(obj.get_object_type() != T::get_type(), {msg, ": woven"})

// The string s contains sub.
`define CHECK_HAS(s, sub, msg) \
  if (!check_pkg::has(s, sub)) check_pkg::fail($sformatf("%s:%0d: %s: '%s' not in:\n%s", \
      `__FILE__, `__LINE__, msg, sub, s));

package check_pkg;
  int unsigned n_checks;

  function automatic void fail(string msg);
    $display("SV_WEAVE_TEST: FAIL %s", msg);
    $fatal(1, "SV_WEAVE_TEST: FAIL %s", msg);
  endfunction

  function automatic bit has(string s, string sub);
    for (int i = 0; i + sub.len() <= s.len(); i++)
      if (s.substr(i, i + sub.len() - 1) == sub)
        return 1;
    return 0;
  endfunction

  function automatic void pass();
    $display("SV_WEAVE_TEST: PASS");
  endfunction
endpackage

`endif
