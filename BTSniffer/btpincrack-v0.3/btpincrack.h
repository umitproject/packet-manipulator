/*
 * Copyright (c) 2006 - David Hulton <dhulton@openciphers.org>
 * see LICENSE for details
 */

#include <sys/types.h>

#define MIN(x, y) ((x) < (y) ? (x) : (y))

u_char *Ar(u_char *, u_char *);			// key, blk -> out 
u_char *Ar_(u_char *, u_char *);		// key, blk -> out
u_char *E22(u_char *, int, u_char *, u_char *);	// pin, pin_l, bd_addr, in_rand -> Kinit
u_char *E21(u_char *, u_char *);		// lk_rand, bd_addr -> Kab
u_char *E1(u_char *, u_char *, u_char *);	// Kab, au_rand, bd_addr -> srand
void hexdump(u_char *, int);			// buf, len
int picoread(unsigned long, void *, unsigned long);
int picowrite(unsigned long, void *, unsigned long);
