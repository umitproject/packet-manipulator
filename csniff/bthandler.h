/*
 * bthandler.h
 *
 *  Created on: Jul 5, 2009
 *      Author: quekshuy
 */

#ifndef BTHANDLER_H_
#define BTHANDLER_H_

#include <Python.h>
#include "btconstants.h"
#include "layers.h"

#define LMP_MASTER 0
#define LMP_SLAVE  1

//
///**
// * Max size of an LMP PDU is 17 bytes.
// * However we put payload as len = 18 so that last is null character. Can be returned as a string.
// */
//typedef struct  {
//
//	PyObject_HEAD
//	uint8_t tid;
//	uint8_t op1;
//	uint8_t op2; //may not exist
//	PyObject *payload;
//
//} __packed PyLMPPacket;
//
//
///**
// * Generic structure for an L2CAPPacket
// */
//typedef struct  {
//
//	PyObject_HEAD
//	PyListObject *data;
//
//} __packed PyGenericPacket;

/**
 * SniffHandler
 */
typedef struct  {

	PyObject_HEAD

}__packed PySniffHandler;


//extern PyTypeObject PyLMPPacketType;
extern PyTypeObject PySniffHandlerType;
//extern PyTypeObject PyGenericPacketType;
#endif /* BTHANDLER_H_ */
