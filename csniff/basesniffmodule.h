#ifndef _basesniffmodule_h_
#define _basesniffmodule_h_

#include <Python.h>
#include "layers.h"
#include "btconstants.h"

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
	int s_llid; //mark for removal
	int s_master; //mark for removal
	int	s_dump; //mark for removal
	int	s_ignore_zero;
	int	s_type; //mark for removal
	uint8_t s_continue;
	uint8_t	s_pin;
	uint8_t	s_pin_data[7][16];
	int	s_pin_master;
	PyObject *bool_resume;
	PyObject *s_pindata;
	PyObject *s_ignore_list;

} __packed PyState;

/**
 * Abstractions for Bluetooth devices
 */

typedef struct {

	PyObject_HEAD
	char *name;
	char *bt_add;

} __packed PyBtDevice;

typedef struct  {

	PyBtDevice dev;
	uint16_t devid;

} __packed PyHCIDevice;

typedef PySniffRaw PySniffUnit;
typedef PyLayerUnit PyLMP;
typedef PyLayerUnit PyL2CAP;

extern PyObject *SniffError;

#ifdef __cplusplus
}
#endif

#endif //_snifmodule_h_
