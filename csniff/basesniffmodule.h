#ifndef _basesniffmodule_h_
#define _basesniffmodule_h_

#include <Python.h>
#define	__packed __attribute__((__packed__))

/**
 * Define firmware version
 */
#define FIRMWARE_47

/* Constants from frontline.c */
#define STATUS_OK		0
#define STATUS_ERROR_HDR	(1 << 2)
#define STATUS_ERROR_LEN	(STATUS_ERROR_HDR | 1)
#define STATUS_ERROR_CRC	(STATUS_ERROR_HDR | (1 << 1)
#define STATUS_UNSUPPORTED	((1 << 3) | 1)

#define HLEN_BC2	0xE
#define HLEN_BC4	0xF

#ifndef FIRMWARE_47 //if firmware v 4.6

#define TYPE_DV		8

#define LMP_IN_RAND	8
#define LMP_COMB_KEY	9
#define LMP_AU_RAND	11
#define LMP_SRES	12

#else

#define TYPE_DV		16

#define LMP_IN_RAND	16
#define LMP_COMB_KEY	18
#define LMP_AU_RAND	22
#define LMP_SRES	24

#endif //FIRMWARE_47


#define FRAG_FIRST      (1 << 6)
#define FRAG_LAST       (1 << 7)
#define CHAN_DEBUG	20

#define FILTER_DATA		1
#define FILTER_SCO		(1 << 1)
#define FILTER_NULL_POLL	(1 << 2)

#define LLID_FRAG	1
#define LLID_START	(1 << 1)
#define LLID_LMP	(LLID_START|LLID_FRAG)

#define CMD_START	0x30
#define CMD_STOP	0x32
#define CMD_FILTER	0x33
#define CMD_TIMER	0x34


#define LMP_TID_MASK	1
#define LMP_OP1_SHIFT	1

#define FP_CLOCK_MASK	0xFFFFFFF
#define FP_SLAVE_MASK	0x2
#define FP_STATUS_SHIFT	28
#define FP_TYPE_SHIFT	3
#define FP_TYPE_MASK	0xF
#define FP_ADDR_MASK	7

#define FP_LEN_LLID_SHIFT	2
#define FP_LEN_LLID_MASK	3
#define FP_LEN_ARQN_MASK	1
#define FP_LEN_SEQN_MASK	(1 << 1)
#define FP_LEN_FLOW		(1 << 4)
#define FP_LEN_SHIFT		5

#define MAX_TYPES 16

#ifdef __cplusplus
extern "C" {
#endif

//define the state object

struct dbg_packet {
	uint8_t 	dp_type;
	uint16_t	dp_unknown1;
	uint16_t	dp_unknown2;
	uint8_t		dp_data[19];
} __packed;


struct start_packet {
	uint8_t		sp_master_rev[6];
	uint32_t	sp_unknown;
	uint8_t		sp_slave_rev[6];
} __packed;


typedef struct {
	PyObject_HEAD
	int	s_fd;
	int	s_buf[1024];
	int	s_len;
	int	s_llid;
	int	s_master;
	int	s_dump;
	int	s_ignore_zero;
	int	s_type;
	uint8_t	s_pin;
	uint8_t	s_pin_data[7][16];
	int	s_pin_master;
	PyObject *s_ignore_list;

} __packed PyState;

struct hcidump_hdr {
	    uint16_t        len;
        uint8_t         in;
        uint8_t         pad;
        uint32_t        ts_sec;
        uint32_t        ts_usec;

}__packed;


struct frontline_packet {
	uint8_t		fp_hlen;
	uint32_t	fp_clock;
	uint8_t		fp_hdr0;
	uint16_t	fp_len;
	uint32_t	fp_timer;
	uint8_t		fp_chan;
	uint8_t		fp_seq;
} __packed;


typedef struct {

	PyObject_HEAD
	int llid;
	int master;
	int type;
	struct frontline_packet *_csrpkt;
	PyObject *_payloadpkt;

} __packed PySniffPacket;

#ifdef __cplusplus
}
#endif

#endif //_snifmodule_h_
