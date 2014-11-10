#cffi binding to libmarpa. you will need libmarpa installed 
#and cffi (install pypy or pip install cffi)
"""
 * 
 * This file is based on Libmarpa, Copyright 2014 Jeffrey Kegler.
 * Libmarpa is free software: you can
 * redistribute it and/or modify it under the terms of the GNU Lesser
 * General Public License as published by the Free Software Foundation,
 * either version 3 of the License, or (at your option) any later version.
 *
 * Libmarpa is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
 * Lesser General Public License for more details.
 *
 * You should have received a copy of the GNU Lesser
 * General Public License along with Libmarpa.  If not, see
 * http://www.gnu.org/licenses/.
 */
"""
import marpa_codes as codes

from cffi import FFI

ffi = FFI()


ffi.cdef(open("marpa.h.cffi.h", "r").read())


lib = ffi.verify("""
#include <marpa.h>
""", libraries=['marpa'])


assert lib.MARPA_MAJOR_VERSION == lib.marpa_major_version
assert lib.MARPA_MINOR_VERSION == lib.marpa_minor_version
assert lib.MARPA_MICRO_VERSION == lib.marpa_micro_version
#ver = ffi.new("int [3]")
#lib.marpa_version(ver)

assert lib.marpa_check_version (lib.MARPA_MAJOR_VERSION ,lib.MARPA_MINOR_VERSION, lib.MARPA_MICRO_VERSION ) == lib.MARPA_ERR_NONE
