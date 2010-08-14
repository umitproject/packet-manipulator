/*
 * Copyright (c) 2006 - David Hulton <dhulton@openciphers.org>
 * see LICENSE for details
 */

#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <string.h>

#include "btpincrack.h"

u_char *
E22(u_char *pin, int l, u_char *bd_addr, u_char *in_rand)
{
	int l_, i;
	u_char pin_[16], in_rand_[16];
	static u_char Kinit[16];

	memcpy(pin_, pin, MIN(l, 16));
	if(l < 16) {
		l_ = MIN(16 - l, 6);
		memcpy(pin_ + l, bd_addr, l_);
		l_ += l;
	} else
		l_ = 16;

	memcpy(in_rand_, in_rand, 16);
	in_rand_[15] ^= l_;

	for(i = l_; i < 16; i++)
		pin_[i] = pin_[i - l_];

	memcpy(Kinit, Ar_(pin_, in_rand_), 16);
//	printf("E22 Kinit: "); hexdump(Kinit, 16);
	return(Kinit);
}

u_char *
E21(u_char *lk_rand, u_char *bd_addr)
{
	int i;
	u_char bd_addr_[16], lk_rand_[16];
	static u_char Kab[16];

	memcpy(lk_rand_, lk_rand, 16);
	lk_rand_[15] ^= 6;

	for(i = 0; i < 16; i++)
		bd_addr_[i] = bd_addr[i % 6];

	memcpy(Kab, Ar_(lk_rand_, bd_addr_), 16);
//	printf("E21 Kab: "); hexdump(Kab, 16);
	return(Kab);
}

u_char *
E1(u_char *Kab, u_char *au_rand, u_char *bd_addr)
{
	int i;
	u_char t[16], Kab_[16];
	static u_char srand[4];

	memcpy(t, Ar(Kab, au_rand), 16);

//	printf("E1 1st: "); hexdump(t, 16);

	for(i = 0; i < 16; i++)
		t[i] = ((t[i] ^ au_rand[i]) + bd_addr[i % 6]) & 0xff;

	Kab_[0 ] = (Kab[0 ] + 233) & 0xff; Kab_[1 ] = Kab[1] ^ 229;
	Kab_[2 ] = (Kab[2 ] + 223) & 0xff; Kab_[3 ] = Kab[3] ^ 193;
	Kab_[4 ] = (Kab[4 ] + 179) & 0xff; Kab_[5 ] = Kab[5] ^ 167;
	Kab_[6 ] = (Kab[6 ] + 149) & 0xff; Kab_[7 ] = Kab[7] ^ 131;
	Kab_[8 ] = Kab[8 ] ^ 233; Kab_[9 ] = (Kab[9 ] + 229) & 0xff;
	Kab_[10] = Kab[10] ^ 223; Kab_[11] = (Kab[11] + 193) & 0xff;
	Kab_[12] = Kab[12] ^ 179; Kab_[13] = (Kab[13] + 167) & 0xff;
	Kab_[14] = Kab[14] ^ 149; Kab_[15] = (Kab[15] + 131) & 0xff;

//	printf("E1 2nd: "); hexdump(Kab_, 16);

	memcpy(srand, Ar_(Kab_, t), 4);
//	printf("E1 sres: "); hexdump(srand, 4);
	return srand;
}
