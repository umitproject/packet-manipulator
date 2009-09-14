
#ifndef BTCONSTANTS_H_
#define BTCONSTANTS_H_


#define	__packed __attribute__((__packed__))

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
#define RETURN_VOID Py_INCREF(Py_None); return Py_None;

#endif /* BTCONSTANTS_H_ */
