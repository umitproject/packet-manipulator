
#ifndef ___moo_marshal_MARSHAL_H__
#define ___moo_marshal_MARSHAL_H__

#include	<glib-object.h>

G_BEGIN_DECLS

/* BOOL:VOID (moomarshals.list:1) */
extern void _moo_marshal_BOOLEAN__VOID (GClosure     *closure,
                                        GValue       *return_value,
                                        guint         n_param_values,
                                        const GValue *param_values,
                                        gpointer      invocation_hint,
                                        gpointer      marshal_data);
#define _moo_marshal_BOOL__VOID	_moo_marshal_BOOLEAN__VOID

/* VOID:INT (moomarshals.list:2) */
#define _moo_marshal_VOID__INT	g_cclosure_marshal_VOID__INT

/* VOID:OBJECT (moomarshals.list:3) */
#define _moo_marshal_VOID__OBJECT	g_cclosure_marshal_VOID__OBJECT

/* VOID:UINT (moomarshals.list:4) */
#define _moo_marshal_VOID__UINT	g_cclosure_marshal_VOID__UINT

G_END_DECLS

#endif /* ___moo_marshal_MARSHAL_H__ */

