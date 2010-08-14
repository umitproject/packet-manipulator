/*
 * This header contains all the protocol data units
 * in a layered fashion.
 *
 */
#ifndef LAYERS_H_
#define LAYERS_H_


#include <Python.h>

#include "btconstants.h"

/**
 * Constants for LMP header manipulation
 */
#define HEADER_LMP_LEN 2
#define LMP_TID_MASK	1
#define LMP_OP1_SHIFT	1

/**
 * Constants for L2CAP header manipulation
 */
#define HEADER_L2CAP_LEN 4
#define MAX_UINT8 255
#define MAX_UINT16 65535
#define MAX_UINT32 4294967295
#define BYTE_BITLEN 8

struct hcidump_hdr {
	    uint16_t        len;
        uint8_t         in;
        uint8_t         pad;
        uint32_t        ts_sec;
        uint32_t        ts_usec;

}__packed;


typedef struct  {

	PyObject_HEAD
	PyObject *rawdata;

} __packed PyRawObject ;


typedef struct {

	PyRawObject raw;

} __packed PyLayerHeader;


typedef struct {

	PyRawObject raw;
	PyLayerHeader *hdr;
	PyRawObject *payload;

} __packed PyLayerUnit;



/**
 * PyLMPHdr inherits PyLayerHeader
 */
typedef struct {

	PyLayerHeader hdr;
	uint8_t tid;
	uint8_t op1;
	uint8_t op2;

} __packed PyLMPHdr;



typedef struct {

	PyLayerHeader hdr;
	uint16_t length;
	uint16_t chan_id;

} __packed PyL2CAPHdr;


/**
 * PyRawObject specific for the frontline tool
 */
struct frontline_packet {
	uint8_t		fp_hlen;
	uint32_t	fp_clock;
	uint8_t		fp_hdr0;
	uint16_t	fp_len;
	uint32_t	fp_timer;
	uint8_t		fp_chan;
	uint8_t		fp_seq;
} __packed;

typedef struct  {
	PyLayerHeader raw;
	uint8_t hlen;
	uint32_t clock;
	uint8_t hdr0;
	uint16_t dlen;
	uint32_t timer;
	uint8_t chan;
	uint8_t seq;

} __packed PySniffHdr;

/**
 * This type is implemented so that additional helper
 * methods can be exposed.
 */
typedef struct {
	PyLayerUnit raw;
}__packed PySniffRaw;


extern PyTypeObject PyRawObjectType;
extern PyTypeObject PyLayerHeaderType;
extern PyTypeObject PyLayerUnitType;
extern PyTypeObject PyLMPHdrType;
extern PyTypeObject PyL2CAPHdrType;
extern PyTypeObject PySniffHdrType;
extern PyTypeObject PySniffRawType;
extern int setup_layer_types(void);
#endif
