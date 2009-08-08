/*
 * This header contains all the protocol data units
 * in a layered fashion.
 *
 */

#include <Python.h>


#define __packed __attribute__((__packed__))

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
#define MAX_UINT16 65535
#define BYTE_BITLEN 8


typedef struct  {

	PyObject_HEAD
	PyObject *data;

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


