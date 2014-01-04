Very simple check for Amanda backup clients

This check uses amcheck and picks up the return code 
as intended by Amanda and also the output.

The return code is *considered* but more strict checks
are done in addition, based on the output.

- Client that isn't known to Amanda:		WARNING
- Client without an index/first backup:  	WARNING
- Client is unreachable:			CRITICAL
- Client denies access:				CRITICAL
- Errors from Amanda: 				WARNING
- Unknown error codes (>3)			UNKNOWN

If none of the above conditions are met then a cross-check 
is done to find if the Client selfcheck is considered OK by Amanda.

In that case, the result is			OK



