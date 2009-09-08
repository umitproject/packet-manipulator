/*
 *   moopaned.c
 *
 *   Copyright (C) 2004-2007 by Yevgen Muntyan <muntyan@math.tamu.edu>
 *
 *   This program is free software; you can redistribute it and/or modify
 *   it under the terms of the GNU General Public License as published by
 *   the Free Software Foundation; either version 2 of the License, or
 *   (at your option) any later version.
 *
 *   See COPYING file that comes with this distribution.
 */

#ifdef HAVE_CONFIG_H
#include "config.h"
#endif

#include "moomarshals.h"
#include "moopaned.h"

#include <string.h>
#include <gdk/gdkkeysyms.h>
#include <gtk/gtk.h>


#ifdef MOO_COMPILATION
# include "mooutils-gobject.h"
#else
# if GLIB_CHECK_VERSION(2,10,0)
#  define MOO_OBJECT_REF_SINK(obj) g_object_ref_sink (obj)
# else
#  define MOO_OBJECT_REF_SINK(obj) gtk_object_sink (g_object_ref (obj))
# endif
#endif


#define MIN_PANE_SIZE 10


typedef enum {
    FOCUS_NONE = 0,
    FOCUS_CHILD,
    FOCUS_PANE,
    FOCUS_BUTTON
} FocusPosition;

struct _MooPanedPrivate {
    MooPanePosition pane_position;

    GdkWindow   *bin_window;
    GdkWindow   *handle_window;
    GdkWindow   *pane_window;

    /* XXX weak pointer */
    gpointer     focus_child; /* focused grandchild of bin->child */
    MooPane     *focus_pane;
    FocusPosition focus;
    gboolean     button_real_focus; /* button was focused by keyboard navigation */
    gboolean     dont_move_focus;   /* do not try to move focus in open_pane/hide_pane */

    MooPane     *current_pane;
    GSList      *panes;

    gboolean     close_on_child_focus;

    int          position;

    gboolean     button_box_visible;
    int          button_box_size;
    gboolean     handle_visible;
    int          handle_size;
    gboolean     pane_widget_visible;
    int          pane_widget_size;
    gboolean     enable_border;
    int          border_size;
    gboolean     sticky;

    gboolean     handle_prelit;
    gboolean     in_drag;
    int          drag_start;

    gboolean     enable_handle_drag;
    gboolean     handle_in_drag;
    gboolean     handle_button_pressed;
    int          handle_drag_start_x;
    int          handle_drag_start_y;
    GdkCursorType handle_cursor_type;

    guint        enable_detaching : 1;
};


static void     moo_paned_set_property      (GObject        *object,
                                             guint           prop_id,
                                             const GValue   *value,
                                             GParamSpec     *pspec);
static void     moo_paned_get_property      (GObject        *object,
                                             guint           prop_id,
                                             GValue         *value,
                                             GParamSpec     *pspec);
static GObject *moo_paned_constructor       (GType                  type,
                                             guint                  n_construct_properties,
                                             GObjectConstructParam *construct_properties);

static void     moo_paned_destroy           (GtkObject      *object);

static void     moo_paned_realize           (GtkWidget      *widget);
static void     moo_paned_unrealize         (GtkWidget      *widget);
static void     moo_paned_map               (GtkWidget      *widget);
static void     moo_paned_unmap             (GtkWidget      *widget);
static gboolean moo_paned_focus             (GtkWidget      *widget,
                                             GtkDirectionType direction);

static void     moo_paned_set_focus_child   (GtkContainer *container,
                                             GtkWidget      *widget);

static void     moo_paned_size_request      (GtkWidget      *widget,
                                             GtkRequisition *requisition);
static void     moo_paned_size_allocate     (GtkWidget      *widget,
                                             GtkAllocation  *allocation);

static gboolean moo_paned_expose            (GtkWidget      *widget,
                                             GdkEventExpose *event);
static gboolean moo_paned_motion            (GtkWidget      *widget,
                                             GdkEventMotion *event);
static gboolean moo_paned_enter             (GtkWidget      *widget,
                                             GdkEventCrossing *event);
static gboolean moo_paned_leave             (GtkWidget      *widget,
                                             GdkEventCrossing *event);
static gboolean moo_paned_button_press      (GtkWidget      *widget,
                                             GdkEventButton *event);
static gboolean moo_paned_button_release    (GtkWidget      *widget,
                                             GdkEventButton *event);
static gboolean moo_paned_key_press         (GtkWidget      *widget,
                                             GdkEventKey    *event);

static int      pane_index                  (MooPaned       *paned,
                                             MooPane        *pane);
static MooPane *get_nth_pane                (MooPaned       *paned,
                                             guint           index_);

static void     moo_paned_open_pane_real    (MooPaned       *paned,
                                             guint           index);
static void     moo_paned_hide_pane_real    (MooPaned       *paned);
static void     moo_paned_set_pane_size_real(MooPaned       *paned,
                                             int             size);

static void     moo_paned_forall            (GtkContainer   *container,
                                             gboolean        include_internals,
                                             GtkCallback     callback,
                                             gpointer        callback_data);
static void     moo_paned_add               (GtkContainer   *container,
                                             GtkWidget      *widget);
static void     moo_paned_remove            (GtkContainer   *container,
                                             GtkWidget      *widget);

static void     realize_handle              (MooPaned       *paned);
static void     realize_pane                (MooPaned       *paned);
static void     draw_handle                 (MooPaned       *paned,
                                             GdkEventExpose *event);
static void     draw_border                 (MooPaned       *paned,
                                             GdkEventExpose *event);
static void     button_box_visible_notify   (MooPaned     *paned);

static void     pane_button_toggled         (GtkToggleButton *button,
                                             MooPaned       *paned);

static gboolean handle_button_press         (GtkWidget      *widget,
                                             GdkEventButton *event,
                                             MooPaned       *paned);
static gboolean handle_button_release       (GtkWidget      *widget,
                                             GdkEventButton *event,
                                             MooPaned       *paned);
static gboolean handle_motion               (GtkWidget      *widget,
                                             GdkEventMotion *event,
                                             MooPaned       *paned);
static gboolean handle_expose               (GtkWidget      *widget,
                                             GdkEventExpose *event,
                                             MooPaned       *paned);
static void     handle_realize              (GtkWidget      *widget,
                                             MooPaned       *paned);

static void     moo_paned_set_handle_cursor_type
                                            (MooPaned       *paned,
                                             GdkCursorType   cursor_type,
                                             gboolean        really_set);
static void     moo_paned_set_enable_detaching
                                            (MooPaned       *paned,
                                             gboolean        enable);

G_DEFINE_TYPE (MooPaned, moo_paned, GTK_TYPE_BIN)

enum {
    PANED_PROP_0,
    PANED_PROP_PANE_POSITION,
    PANED_PROP_CLOSE_PANE_ON_CHILD_FOCUS,
    PANED_PROP_STICKY_PANE,
    PANED_PROP_ENABLE_HANDLE_DRAG,
    PANED_PROP_HANDLE_CURSOR_TYPE,
    PANED_PROP_ENABLE_DETACHING,
    PANED_PROP_ENABLE_BORDER
};

enum {
    PANED_SET_PANE_SIZE,
    PANED_HANDLE_DRAG_START,
    PANED_HANDLE_DRAG_MOTION,
    PANED_HANDLE_DRAG_END,
    PANED_PANE_PARAMS_CHANGED,
    PANED_NUM_SIGNALS
};

static guint paned_signals[PANED_NUM_SIGNALS];

static void
moo_paned_class_init (MooPanedClass *klass)
{
    GObjectClass *gobject_class = G_OBJECT_CLASS (klass);
    GtkObjectClass *gtkobject_class = GTK_OBJECT_CLASS (klass);
    GtkWidgetClass *widget_class = GTK_WIDGET_CLASS (klass);
    GtkContainerClass *container_class = GTK_CONTAINER_CLASS (klass);

    g_type_class_add_private (klass, sizeof (MooPanedPrivate));

    gobject_class->set_property = moo_paned_set_property;
    gobject_class->get_property = moo_paned_get_property;
    gobject_class->constructor = moo_paned_constructor;

    gtkobject_class->destroy = moo_paned_destroy;

    widget_class->realize = moo_paned_realize;
    widget_class->unrealize = moo_paned_unrealize;
    widget_class->map = moo_paned_map;
    widget_class->unmap = moo_paned_unmap;
    widget_class->expose_event = moo_paned_expose;
    widget_class->size_request = moo_paned_size_request;
    widget_class->size_allocate = moo_paned_size_allocate;
    widget_class->motion_notify_event = moo_paned_motion;
    widget_class->enter_notify_event = moo_paned_enter;
    widget_class->leave_notify_event = moo_paned_leave;
    widget_class->button_press_event = moo_paned_button_press;
    widget_class->button_release_event = moo_paned_button_release;
    widget_class->focus = moo_paned_focus;
    widget_class->key_press_event = moo_paned_key_press;

    container_class->forall = moo_paned_forall;
    container_class->set_focus_child = moo_paned_set_focus_child;
    container_class->remove = moo_paned_remove;
    container_class->add = moo_paned_add;

    klass->set_pane_size = moo_paned_set_pane_size_real;

    g_object_class_install_property (gobject_class,
                                     PANED_PROP_PANE_POSITION,
                                     g_param_spec_enum ("pane-position",
                                             "pane-position",
                                             "pane-position",
                                             MOO_TYPE_PANE_POSITION,
                                             MOO_PANE_POS_LEFT,
                                             G_PARAM_READWRITE |
                                                     G_PARAM_CONSTRUCT_ONLY));

    g_object_class_install_property (gobject_class,
                                     PANED_PROP_CLOSE_PANE_ON_CHILD_FOCUS,
                                     g_param_spec_boolean ("close-pane-on-child-focus",
                                             "close-pane-on-child-focus",
                                             "close-pane-on-child-focus",
                                             TRUE,
                                             G_PARAM_READWRITE | G_PARAM_CONSTRUCT));

    g_object_class_install_property (gobject_class,
                                     PANED_PROP_STICKY_PANE,
                                     g_param_spec_boolean ("sticky-pane",
                                             "sticky-pane",
                                             "sticky-pane",
                                             FALSE,
                                             G_PARAM_READWRITE | G_PARAM_CONSTRUCT));

    g_object_class_install_property (gobject_class,
                                     PANED_PROP_ENABLE_HANDLE_DRAG,
                                     g_param_spec_boolean ("enable-handle-drag",
                                             "enable-handle-drag",
                                             "enable-handle-drag",
                                             FALSE,
                                             G_PARAM_READWRITE));

    g_object_class_install_property (gobject_class,
                                     PANED_PROP_ENABLE_DETACHING,
                                     g_param_spec_boolean ("enable-detaching",
                                             "enable-detaching",
                                             "enable-detaching",
                                             FALSE,
                                             G_PARAM_READWRITE | G_PARAM_CONSTRUCT));

    g_object_class_install_property (gobject_class,
                                     PANED_PROP_HANDLE_CURSOR_TYPE,
                                     g_param_spec_enum ("handle-cursor-type",
                                             "handle-cursor-type",
                                             "handle-cursor-type",
                                             GDK_TYPE_CURSOR_TYPE,
                                             GDK_HAND2,
                                             G_PARAM_CONSTRUCT | G_PARAM_READWRITE));

    g_object_class_install_property (gobject_class,
                                     PANED_PROP_ENABLE_BORDER,
                                     g_param_spec_boolean ("enable-border",
                                             "enable-border",
                                             "enable-border",
                                             TRUE,
                                             G_PARAM_CONSTRUCT | G_PARAM_READWRITE));

    gtk_widget_class_install_style_property (widget_class,
                                             g_param_spec_int ("handle-size",
                                                     "handle-size",
                                                     "handle-size",
                                                     0,
                                                     G_MAXINT,
                                                     5,
                                                     G_PARAM_READABLE));

    gtk_widget_class_install_style_property (widget_class,
                                             g_param_spec_int ("button-spacing",
                                                     "button-spacing",
                                                     "button-spacing",
                                                     0,
                                                     G_MAXINT,
                                                     0,
                                                     G_PARAM_READABLE));

    paned_signals[PANED_SET_PANE_SIZE] =
            g_signal_new ("set-pane-size",
                          G_OBJECT_CLASS_TYPE (klass),
                          G_SIGNAL_RUN_FIRST | G_SIGNAL_ACTION,
                          G_STRUCT_OFFSET (MooPanedClass, set_pane_size),
                          NULL, NULL,
                          _moo_marshal_VOID__INT,
                          G_TYPE_NONE, 1,
                          G_TYPE_INT);

    paned_signals[PANED_HANDLE_DRAG_START] =
            g_signal_new ("handle-drag-start",
                          G_OBJECT_CLASS_TYPE (klass),
                          G_SIGNAL_RUN_FIRST,
                          G_STRUCT_OFFSET (MooPanedClass, handle_drag_start),
                          NULL, NULL,
                          _moo_marshal_VOID__OBJECT,
                          G_TYPE_NONE, 1,
                          GTK_TYPE_WIDGET);

    paned_signals[PANED_HANDLE_DRAG_MOTION] =
            g_signal_new ("handle-drag-motion",
                          G_OBJECT_CLASS_TYPE (klass),
                          G_SIGNAL_RUN_FIRST,
                          G_STRUCT_OFFSET (MooPanedClass, handle_drag_motion),
                          NULL, NULL,
                          _moo_marshal_VOID__OBJECT,
                          G_TYPE_NONE, 1,
                          GTK_TYPE_WIDGET);

    paned_signals[PANED_HANDLE_DRAG_END] =
            g_signal_new ("handle-drag-end",
                          G_OBJECT_CLASS_TYPE (klass),
                          G_SIGNAL_RUN_FIRST,
                          G_STRUCT_OFFSET (MooPanedClass, handle_drag_end),
                          NULL, NULL,
                          _moo_marshal_VOID__OBJECT,
                          G_TYPE_NONE, 1,
                          GTK_TYPE_WIDGET);

    paned_signals[PANED_PANE_PARAMS_CHANGED] =
            g_signal_new ("pane-params-changed",
                          G_OBJECT_CLASS_TYPE (klass),
                          G_SIGNAL_RUN_LAST,
                          G_STRUCT_OFFSET (MooPanedClass, pane_params_changed),
                          NULL, NULL,
                          _moo_marshal_VOID__UINT,
                          G_TYPE_NONE, 1,
                          G_TYPE_UINT);
}


static void
moo_paned_init (MooPaned *paned)
{
    GTK_WIDGET_SET_FLAGS (paned, GTK_NO_WINDOW);

    paned->priv = G_TYPE_INSTANCE_GET_PRIVATE (paned,
                                               MOO_TYPE_PANED,
                                               MooPanedPrivate);

    paned->button_box = NULL;

    paned->priv->pane_position = -1;
    paned->priv->handle_window = NULL;
    paned->priv->pane_window = NULL;
    paned->priv->bin_window = NULL;
    paned->priv->current_pane = NULL;
    paned->priv->panes = NULL;
    paned->priv->enable_border = TRUE;
    paned->priv->button_box_visible = FALSE;
    paned->priv->button_box_size = 0;
    paned->priv->handle_visible = FALSE;
    paned->priv->handle_size = 0;
    paned->priv->pane_widget_visible = FALSE;
    paned->priv->pane_widget_size = 0;
    paned->priv->sticky = FALSE;
    paned->priv->position = -1;
    paned->priv->handle_prelit = FALSE;
    paned->priv->in_drag = FALSE;
    paned->priv->drag_start = -1;
}


static GObject*
moo_paned_constructor (GType                  type,
                       guint                  n_construct_properties,
                       GObjectConstructParam *construct_properties)
{
    GObject *object;
    MooPaned *paned;
    int button_spacing;

    object = G_OBJECT_CLASS(moo_paned_parent_class)->constructor (type,
                                n_construct_properties, construct_properties);
    paned = MOO_PANED (object);

    gtk_widget_style_get (GTK_WIDGET (paned),
                          "button-spacing", &button_spacing, NULL);

    switch (paned->priv->pane_position)
    {
        case MOO_PANE_POS_LEFT:
        case MOO_PANE_POS_RIGHT:
            paned->button_box = gtk_vbox_new (FALSE, button_spacing);
            break;
        case MOO_PANE_POS_TOP:
        case MOO_PANE_POS_BOTTOM:
            paned->button_box = gtk_hbox_new (FALSE, button_spacing);
            break;
        default:
            g_warning ("%s: invalid 'pane-position' property value '%u',"
                       "falling back to MOO_PANE_POS_LEFT", G_STRLOC,
                       paned->priv->pane_position);
            paned->priv->pane_position = MOO_PANE_POS_LEFT;
            paned->button_box = gtk_vbox_new (FALSE, button_spacing);
            break;
    }

    MOO_OBJECT_REF_SINK (paned->button_box);
    gtk_widget_set_parent_window (paned->button_box, paned->priv->bin_window);
    gtk_widget_set_parent (paned->button_box, GTK_WIDGET (paned));
    gtk_widget_show (paned->button_box);
    g_signal_connect_swapped (paned->button_box, "notify::visible",
                              G_CALLBACK (button_box_visible_notify),
                              paned);

    return object;
}


static void
moo_paned_set_property (GObject        *object,
                        guint           prop_id,
                        const GValue   *value,
                        GParamSpec     *pspec)
{
    MooPaned *paned = MOO_PANED (object);

    switch (prop_id)
    {
        case PANED_PROP_PANE_POSITION:
            paned->priv->pane_position = g_value_get_enum (value);
            break;

        case PANED_PROP_CLOSE_PANE_ON_CHILD_FOCUS:
            paned->priv->close_on_child_focus =
                    g_value_get_boolean (value);
            g_object_notify (object, "close-pane-on-child-focus");
            break;

        case PANED_PROP_ENABLE_BORDER:
            paned->priv->enable_border = g_value_get_boolean (value);
            gtk_widget_queue_resize (GTK_WIDGET (paned));
            g_object_notify (object, "enable_border");
            break;

        case PANED_PROP_STICKY_PANE:
            moo_paned_set_sticky_pane (paned,
                                       g_value_get_boolean (value));
            break;

        case PANED_PROP_ENABLE_HANDLE_DRAG:
            paned->priv->enable_handle_drag = g_value_get_boolean (value);
            if (!paned->priv->enable_handle_drag)
                moo_paned_set_handle_cursor_type (paned, 0, FALSE);
            else
                moo_paned_set_handle_cursor_type (paned, paned->priv->handle_cursor_type, TRUE);
            g_object_notify (object, "enable-handle-drag");
            break;

        case PANED_PROP_ENABLE_DETACHING:
            moo_paned_set_enable_detaching (paned, g_value_get_boolean (value));
            break;

        case PANED_PROP_HANDLE_CURSOR_TYPE:
            if (paned->priv->enable_handle_drag)
                moo_paned_set_handle_cursor_type (paned, g_value_get_enum (value), TRUE);
            else
                paned->priv->handle_cursor_type = g_value_get_enum (value);
            break;

        default:
            G_OBJECT_WARN_INVALID_PROPERTY_ID (object, prop_id, pspec);
    }
}


static void
moo_paned_get_property (GObject        *object,
                        guint           prop_id,
                        GValue         *value,
                        GParamSpec     *pspec)
{
    MooPaned *paned = MOO_PANED (object);

    switch (prop_id)
    {
        case PANED_PROP_PANE_POSITION:
            g_value_set_enum (value, paned->priv->pane_position);
            break;

        case PANED_PROP_CLOSE_PANE_ON_CHILD_FOCUS:
            g_value_set_boolean (value, paned->priv->close_on_child_focus);
            break;

        case PANED_PROP_STICKY_PANE:
            g_value_set_boolean (value, paned->priv->sticky);
            break;

        case PANED_PROP_ENABLE_HANDLE_DRAG:
            g_value_set_boolean (value, paned->priv->enable_handle_drag);
            break;

        case PANED_PROP_ENABLE_BORDER:
            g_value_set_boolean (value, paned->priv->enable_border);
            break;

        case PANED_PROP_ENABLE_DETACHING:
            g_value_set_boolean (value, paned->priv->enable_detaching ? TRUE : FALSE);
            break;

        case PANED_PROP_HANDLE_CURSOR_TYPE:
            g_value_set_enum (value, paned->priv->handle_cursor_type);
            break;

        default:
            G_OBJECT_WARN_INVALID_PROPERTY_ID (object, prop_id, pspec);
    }
}


static void
moo_paned_destroy (GtkObject      *object)
{
    GSList *l;
    MooPaned *paned = MOO_PANED (object);

    for (l = paned->priv->panes; l != NULL; l = l->next)
        gtk_object_destroy (l->data);

    GTK_OBJECT_CLASS(moo_paned_parent_class)->destroy (object);

    for (l = paned->priv->panes; l != NULL; l = l->next)
        g_object_unref (l->data);

    g_slist_free (paned->priv->panes);
    paned->priv->panes = NULL;
}


GtkWidget*
moo_paned_new (MooPanePosition pane_position)
{
    return GTK_WIDGET (g_object_new (MOO_TYPE_PANED,
                       "pane-position", pane_position,
                       NULL));
}


MooPanePosition
_moo_paned_get_position (MooPaned *paned)
{
    g_return_val_if_fail (MOO_IS_PANED (paned), 0);
    return paned->priv->pane_position;
}


static void
moo_paned_realize (GtkWidget       *widget)
{
    static GdkWindowAttr attributes;
    gint attributes_mask;
    MooPaned *paned;

    paned = MOO_PANED (widget);

    GTK_WIDGET_SET_FLAGS (widget, GTK_REALIZED);

    widget->window = gtk_widget_get_parent_window (widget);
    g_object_ref (widget->window);

    attributes.x = widget->allocation.x;
    attributes.y = widget->allocation.y;
    attributes.width = widget->allocation.width;
    attributes.height = widget->allocation.height;
    attributes.window_type = GDK_WINDOW_CHILD;
    attributes.event_mask = gtk_widget_get_events (widget)
            | GDK_EXPOSURE_MASK;

    attributes.visual = gtk_widget_get_visual (widget);
    attributes.colormap = gtk_widget_get_colormap (widget);
    attributes.wclass = GDK_INPUT_OUTPUT;

    attributes_mask = GDK_WA_X | GDK_WA_Y | GDK_WA_VISUAL | GDK_WA_COLORMAP;

    paned->priv->bin_window = gdk_window_new (gtk_widget_get_parent_window (widget),
                                              &attributes, attributes_mask);
    gdk_window_set_user_data (paned->priv->bin_window, widget);

    widget->style = gtk_style_attach (widget->style, widget->window);
    gtk_style_set_background (widget->style, paned->priv->bin_window, GTK_STATE_NORMAL);

    realize_pane (paned);

    if (paned->button_box)
        gtk_widget_set_parent_window (paned->button_box, paned->priv->bin_window);
    if (GTK_BIN(paned)->child)
        gtk_widget_set_parent_window (GTK_BIN(paned)->child, paned->priv->bin_window);
}


static void
realize_handle (MooPaned *paned)
{
    static GdkWindowAttr attributes;
    gint attributes_mask;
    GtkWidget *widget = GTK_WIDGET (paned);

    switch (paned->priv->pane_position)
    {
        case MOO_PANE_POS_LEFT:
        case MOO_PANE_POS_RIGHT:
            attributes.y = 0;
            attributes.width = paned->priv->handle_size;
            attributes.height = widget->allocation.height;
            break;
        case MOO_PANE_POS_TOP:
        case MOO_PANE_POS_BOTTOM:
            attributes.x = 0;
            attributes.width = widget->allocation.width;
            attributes.height = paned->priv->handle_size;
            break;
    }

    switch (paned->priv->pane_position)
    {
        case MOO_PANE_POS_LEFT:
            attributes.x = paned->priv->pane_widget_size;
            break;
        case MOO_PANE_POS_RIGHT:
            attributes.x = 0;
            break;
        case MOO_PANE_POS_TOP:
            attributes.y = paned->priv->pane_widget_size;
            break;
        case MOO_PANE_POS_BOTTOM:
            attributes.y = 0;
            break;
    }

    attributes.window_type = GDK_WINDOW_CHILD;
    attributes.event_mask = gtk_widget_get_events (widget)
            | GDK_POINTER_MOTION_HINT_MASK
            | GDK_POINTER_MOTION_MASK
            | GDK_BUTTON_PRESS_MASK
            | GDK_BUTTON_RELEASE_MASK
            | GDK_EXPOSURE_MASK
            | GDK_ENTER_NOTIFY_MASK
            | GDK_LEAVE_NOTIFY_MASK;

    attributes.visual = gtk_widget_get_visual (widget);
    attributes.colormap = gtk_widget_get_colormap (widget);
    attributes.wclass = GDK_INPUT_OUTPUT;

    switch (paned->priv->pane_position)
    {
        case MOO_PANE_POS_LEFT:
        case MOO_PANE_POS_RIGHT:
            attributes.cursor = gdk_cursor_new (GDK_SB_H_DOUBLE_ARROW);
            break;
        case MOO_PANE_POS_TOP:
        case MOO_PANE_POS_BOTTOM:
            attributes.cursor = gdk_cursor_new (GDK_SB_V_DOUBLE_ARROW);
            break;
    }

    attributes_mask = GDK_WA_X | GDK_WA_Y | GDK_WA_VISUAL |
            GDK_WA_COLORMAP | GDK_WA_CURSOR;

    paned->priv->handle_window = gdk_window_new (paned->priv->pane_window,
            &attributes, attributes_mask);
    gdk_window_set_user_data (paned->priv->handle_window, widget);

    gtk_style_set_background (widget->style,
                              paned->priv->handle_window,
                              GTK_STATE_NORMAL);

    gdk_cursor_unref (attributes.cursor);
}


static void
get_pane_window_rect (MooPaned     *paned,
                      GdkRectangle *rect)
{
    *rect = GTK_WIDGET(paned)->allocation;

    switch (paned->priv->pane_position)
    {
        case MOO_PANE_POS_LEFT:
        case MOO_PANE_POS_RIGHT:
            rect->width = paned->priv->pane_widget_size + paned->priv->handle_size;
            break;
        case MOO_PANE_POS_TOP:
        case MOO_PANE_POS_BOTTOM:
            rect->height = paned->priv->pane_widget_size + paned->priv->handle_size;
            break;
    }

    switch (paned->priv->pane_position)
    {
        case MOO_PANE_POS_LEFT:
            rect->x += paned->priv->button_box_size;
            break;
        case MOO_PANE_POS_RIGHT:
            rect->x += GTK_WIDGET(paned)->allocation.width - rect->width -
                            paned->priv->button_box_size;
            break;
        case MOO_PANE_POS_TOP:
            rect->y += paned->priv->button_box_size;
            break;
        case MOO_PANE_POS_BOTTOM:
            rect->y += GTK_WIDGET(paned)->allocation.height - rect->height -
                            paned->priv->button_box_size;
            break;
    }
}


static void
realize_pane (MooPaned *paned)
{
    static GdkWindowAttr attributes;
    gint attributes_mask;
    GtkWidget *widget = GTK_WIDGET (paned);
    GdkRectangle rect;

    get_pane_window_rect (paned, &rect);
    attributes.x = rect.x;
    attributes.y = rect.y;
    attributes.width = rect.width;
    attributes.height = rect.height;

    attributes.window_type = GDK_WINDOW_CHILD;
    attributes.event_mask = gtk_widget_get_events (widget)
            | GDK_EXPOSURE_MASK;

    attributes.visual = gtk_widget_get_visual (widget);
    attributes.colormap = gtk_widget_get_colormap (widget);
    attributes.wclass = GDK_INPUT_OUTPUT;

    attributes_mask = GDK_WA_X | GDK_WA_Y | GDK_WA_VISUAL |
            GDK_WA_COLORMAP;

    paned->priv->pane_window =
            gdk_window_new (widget->window, &attributes, attributes_mask);
    gdk_window_set_user_data (paned->priv->pane_window, widget);

    gtk_style_set_background (widget->style,
                              paned->priv->pane_window,
                              GTK_STATE_NORMAL);

    realize_handle (paned);
}


static void
moo_paned_unrealize (GtkWidget *widget)
{
    MooPaned *paned = MOO_PANED (widget);

    if (paned->priv->handle_window)
    {
        gdk_window_set_user_data (paned->priv->handle_window, NULL);
        gdk_window_destroy (paned->priv->handle_window);
        paned->priv->handle_window = NULL;
        paned->priv->handle_visible = FALSE;
        paned->priv->handle_size = 0;
    }

    if (paned->priv->pane_window)
    {
        gdk_window_set_user_data (paned->priv->pane_window, NULL);
        gdk_window_destroy (paned->priv->pane_window);
        paned->priv->pane_window = NULL;
        paned->priv->pane_widget_visible = FALSE;
        paned->priv->pane_widget_size = 0;
    }

    if (paned->priv->bin_window)
    {
        gdk_window_set_user_data (paned->priv->bin_window, NULL);
        gdk_window_destroy (paned->priv->bin_window);
        paned->priv->bin_window = NULL;
    }

    GTK_WIDGET_CLASS(moo_paned_parent_class)->unrealize (widget);
}


static void
add_button_box_requisition (MooPaned *paned,
                            GtkRequisition *requisition,
                            GtkRequisition *child_requisition)
{
    switch (paned->priv->pane_position)
    {
        case MOO_PANE_POS_LEFT:
        case MOO_PANE_POS_RIGHT:
            requisition->width += child_requisition->width;
            requisition->height = MAX (child_requisition->height, requisition->height);
            paned->priv->button_box_size = child_requisition->width;
            break;
        case MOO_PANE_POS_TOP:
        case MOO_PANE_POS_BOTTOM:
            requisition->height += child_requisition->height;
            requisition->width = MAX (child_requisition->width, requisition->width);
            paned->priv->button_box_size = child_requisition->height;
            break;
    }
}


static void
add_handle_requisition (MooPaned       *paned,
                        GtkRequisition *requisition)
{
    gtk_widget_style_get (GTK_WIDGET (paned),
                          "handle_size", &paned->priv->handle_size,
                          NULL);

    switch (paned->priv->pane_position)
    {
        case MOO_PANE_POS_LEFT:
        case MOO_PANE_POS_RIGHT:
            requisition->width += paned->priv->handle_size;
            break;
        case MOO_PANE_POS_TOP:
        case MOO_PANE_POS_BOTTOM:
            requisition->height += paned->priv->handle_size;
            break;
    }
}


static void
add_pane_widget_requisition (MooPaned       *paned,
                             GtkRequisition *requisition,
                             GtkRequisition *child_requisition)
{
    switch (paned->priv->pane_position)
    {
        case MOO_PANE_POS_LEFT:
        case MOO_PANE_POS_RIGHT:
            requisition->height = MAX (child_requisition->height, requisition->height);

            if (paned->priv->sticky)
            {
                requisition->width += child_requisition->width;
            }
            else
            {
                requisition->width = MAX (child_requisition->width +
                        paned->priv->button_box_size +
                        paned->priv->handle_size, requisition->width);
            }

            break;

        case MOO_PANE_POS_TOP:
        case MOO_PANE_POS_BOTTOM:
            requisition->width = MAX (child_requisition->width, requisition->width);

            if (paned->priv->sticky)
            {
                requisition->height += child_requisition->height;
            }
            else
            {
                requisition->height = MAX (child_requisition->height +
                        paned->priv->button_box_size +
                        paned->priv->handle_size, requisition->height);
            }

            break;
    }

    switch (paned->priv->pane_position)
    {
        case MOO_PANE_POS_LEFT:
        case MOO_PANE_POS_RIGHT:
            paned->priv->pane_widget_size = MAX (paned->priv->position,
                    child_requisition->width);
            paned->priv->position = paned->priv->pane_widget_size;
            break;
        case MOO_PANE_POS_TOP:
        case MOO_PANE_POS_BOTTOM:
            paned->priv->pane_widget_size = MAX (paned->priv->position,
                    child_requisition->height);
            paned->priv->position = paned->priv->pane_widget_size;
            break;
    }
}


static void
moo_paned_size_request (GtkWidget      *widget,
                        GtkRequisition *requisition)
{
    GtkBin *bin = GTK_BIN (widget);
    MooPaned *paned = MOO_PANED (widget);
    GtkRequisition child_requisition;

    requisition->width = 0;
    requisition->height = 0;

    if (bin->child && GTK_WIDGET_VISIBLE (bin->child))
    {
        gtk_widget_size_request (bin->child, &child_requisition);
        requisition->width += child_requisition.width;
        requisition->height += child_requisition.height;
    }

    if (paned->priv->button_box_visible)
    {
        gtk_widget_size_request (paned->button_box, &child_requisition);
        add_button_box_requisition (paned, requisition, &child_requisition);
    }
    else
    {
        paned->priv->button_box_size = 0;
    }

    if (paned->priv->handle_visible)
        add_handle_requisition (paned, requisition);
    else
        paned->priv->handle_size = 0;

    if (paned->priv->pane_widget_visible)
    {
        _moo_pane_size_request (paned->priv->current_pane, &child_requisition);
        add_pane_widget_requisition (paned, requisition, &child_requisition);
    }
    else
    {
        paned->priv->pane_widget_size = 0;
    }

    if (paned->priv->enable_border)
    {
        switch (paned->priv->pane_position)
        {
            case MOO_PANE_POS_LEFT:
            case MOO_PANE_POS_RIGHT:
                paned->priv->border_size = widget->style->xthickness;
                requisition->width += paned->priv->border_size;
                break;
            case MOO_PANE_POS_TOP:
            case MOO_PANE_POS_BOTTOM:
                paned->priv->border_size = widget->style->ythickness;
                requisition->height += paned->priv->border_size;
                break;
        }
    }
    else
    {
        paned->priv->border_size = 0;
    }
}


static void
get_pane_widget_allocation (MooPaned        *paned,
                            GtkAllocation   *allocation)
{
    allocation->x = 0;
    allocation->y = 0;
    allocation->width = GTK_WIDGET(paned)->allocation.width;
    allocation->height = GTK_WIDGET(paned)->allocation.height;

    switch (paned->priv->pane_position)
    {
        case MOO_PANE_POS_RIGHT:
            allocation->x += paned->priv->handle_size;
            /* fall through */
        case MOO_PANE_POS_LEFT:
            allocation->width = paned->priv->pane_widget_size;
            break;

        case MOO_PANE_POS_BOTTOM:
            allocation->y += paned->priv->handle_size;
            /* fall through */
        case MOO_PANE_POS_TOP:
            allocation->height = paned->priv->pane_widget_size;
            break;
    }
}


static void
get_button_box_allocation (MooPaned        *paned,
                           GtkAllocation   *allocation)
{
    switch (paned->priv->pane_position)
    {
        case MOO_PANE_POS_LEFT:
        case MOO_PANE_POS_RIGHT:
            allocation->y = 0;
            allocation->height = GTK_WIDGET(paned)->allocation.height;
            allocation->width = paned->priv->button_box_size;
            break;
        case MOO_PANE_POS_TOP:
        case MOO_PANE_POS_BOTTOM:
            allocation->x = 0;
            allocation->width = GTK_WIDGET(paned)->allocation.width;
            allocation->height = paned->priv->button_box_size;
            break;
    }

    switch (paned->priv->pane_position)
    {
        case MOO_PANE_POS_LEFT:
            allocation->x = 0;
            break;
        case MOO_PANE_POS_RIGHT:
            allocation->x = GTK_WIDGET(paned)->allocation.width - allocation->width;
            break;
        case MOO_PANE_POS_TOP:
            allocation->y = 0;
            break;
        case MOO_PANE_POS_BOTTOM:
            allocation->y = GTK_WIDGET(paned)->allocation.height - allocation->height;
            break;
    }
}


static void
get_bin_child_allocation (MooPaned        *paned,
                          GtkAllocation   *allocation)
{
    switch (paned->priv->pane_position)
    {
        case MOO_PANE_POS_LEFT:
        case MOO_PANE_POS_RIGHT:
            allocation->y = 0;
            allocation->height = GTK_WIDGET(paned)->allocation.height;
            allocation->width = GTK_WIDGET(paned)->allocation.width -
                                paned->priv->button_box_size -
                                paned->priv->border_size;
            break;
        case MOO_PANE_POS_TOP:
        case MOO_PANE_POS_BOTTOM:
            allocation->x = 0;
            allocation->width = GTK_WIDGET(paned)->allocation.width;
            allocation->height = GTK_WIDGET(paned)->allocation.height -
                                 paned->priv->button_box_size -
                                 paned->priv->border_size;
            break;
    }

    switch (paned->priv->pane_position)
    {
        case MOO_PANE_POS_LEFT:
            allocation->x = paned->priv->button_box_size +
                            paned->priv->border_size;
            break;
        case MOO_PANE_POS_RIGHT:
            allocation->x = 0;
            break;
        case MOO_PANE_POS_TOP:
            allocation->y = paned->priv->button_box_size +
                            paned->priv->border_size;
            break;
        case MOO_PANE_POS_BOTTOM:
            allocation->y = 0;
            break;
    }

    if (paned->priv->sticky)
    {
        int add = paned->priv->handle_size + paned->priv->pane_widget_size;

        switch (paned->priv->pane_position)
        {
            case MOO_PANE_POS_LEFT:
                allocation->x += add;
                allocation->width -= add;
                break;
            case MOO_PANE_POS_RIGHT:
                allocation->width -= add;
                break;
            case MOO_PANE_POS_TOP:
                allocation->y += add;
                allocation->height -= add;
                break;
            case MOO_PANE_POS_BOTTOM:
                allocation->height -= add;
                break;
        }
    }
}


static void
clamp_handle_size (MooPaned *paned)
{
    switch (paned->priv->pane_position)
    {
        case MOO_PANE_POS_LEFT:
        case MOO_PANE_POS_RIGHT:
            paned->priv->handle_size = CLAMP (paned->priv->handle_size, 0,
                                              GTK_WIDGET(paned)->allocation.width);
            break;
        case MOO_PANE_POS_TOP:
        case MOO_PANE_POS_BOTTOM:
            paned->priv->handle_size = CLAMP (paned->priv->handle_size, 0,
                                              GTK_WIDGET(paned)->allocation.height);
            break;
    }
}


static void
clamp_button_box_size (MooPaned *paned)
{
    switch (paned->priv->pane_position)
    {
        case MOO_PANE_POS_LEFT:
        case MOO_PANE_POS_RIGHT:
            paned->priv->button_box_size = CLAMP (paned->priv->button_box_size, 0,
                    GTK_WIDGET(paned)->allocation.width -
                            paned->priv->handle_size);
            break;
        case MOO_PANE_POS_TOP:
        case MOO_PANE_POS_BOTTOM:
            paned->priv->button_box_size = CLAMP (paned->priv->button_box_size, 0,
                    GTK_WIDGET(paned)->allocation.height -
                            paned->priv->handle_size);
            break;
    }
}


static void
clamp_child_requisition (MooPaned *paned,
                         GtkRequisition *requisition)
{
    switch (paned->priv->pane_position)
    {
        case MOO_PANE_POS_LEFT:
        case MOO_PANE_POS_RIGHT:
            requisition->width = CLAMP (requisition->width, 0,
                                        GTK_WIDGET(paned)->allocation.width -
                                                paned->priv->handle_size -
                                                paned->priv->button_box_size -
                                                paned->priv->border_size);
            break;
        case MOO_PANE_POS_TOP:
        case MOO_PANE_POS_BOTTOM:
            requisition->height = CLAMP (requisition->height, 0,
                                        GTK_WIDGET(paned)->allocation.height -
                                                paned->priv->handle_size -
                                                paned->priv->button_box_size -
                                                paned->priv->border_size);
            break;
    }
}


static void
clamp_pane_widget_size (MooPaned       *paned,
                        GtkRequisition *child_requisition)
{
    int min_size;
    int max_size = 0;

    switch (paned->priv->pane_position)
    {
        case MOO_PANE_POS_LEFT:
        case MOO_PANE_POS_RIGHT:
            max_size = GTK_WIDGET(paned)->allocation.width -
                                      paned->priv->handle_size -
                                      paned->priv->button_box_size;
            if (paned->priv->sticky)
                max_size -= child_requisition->width;
            break;
        case MOO_PANE_POS_TOP:
        case MOO_PANE_POS_BOTTOM:
            max_size = GTK_WIDGET(paned)->allocation.height -
                                      paned->priv->handle_size -
                                      paned->priv->button_box_size;
            if (paned->priv->sticky)
                max_size -= child_requisition->height;
            break;
    }

    min_size = CLAMP (MIN_PANE_SIZE, 0, max_size);

    paned->priv->pane_widget_size =
        CLAMP (paned->priv->pane_widget_size, min_size, max_size);
}


static void
get_handle_window_rect (MooPaned      *paned,
                        GdkRectangle  *rect)
{
    switch (paned->priv->pane_position)
    {
        case MOO_PANE_POS_LEFT:
        case MOO_PANE_POS_RIGHT:
            rect->y = 0;
            rect->width = paned->priv->handle_size;
            rect->height = GTK_WIDGET(paned)->allocation.height;
            break;
        case MOO_PANE_POS_TOP:
        case MOO_PANE_POS_BOTTOM:
            rect->x = 0;
            rect->height = paned->priv->handle_size;
            rect->width = GTK_WIDGET(paned)->allocation.width;
            break;
    }

    switch (paned->priv->pane_position)
    {
        case MOO_PANE_POS_LEFT:
            rect->x = paned->priv->pane_widget_size;
            break;
        case MOO_PANE_POS_RIGHT:
            rect->x = 0;
            break;
        case MOO_PANE_POS_TOP:
            rect->y = paned->priv->pane_widget_size;
            break;
        case MOO_PANE_POS_BOTTOM:
            rect->y = 0;
            break;
    }
}


static void
moo_paned_size_allocate (GtkWidget     *widget,
                         GtkAllocation *allocation)
{
    GtkBin *bin;
    MooPaned *paned;
    GtkAllocation child_allocation;
    GtkRequisition child_requisition = {0, 0};

    widget->allocation = *allocation;
    bin = GTK_BIN (widget);
    paned = MOO_PANED (widget);

    if (!paned->priv->handle_visible)
        paned->priv->handle_size = 0;
    if (!paned->priv->button_box_visible)
        paned->priv->button_box_size = 0;
    if (!paned->priv->pane_widget_visible)
        paned->priv->pane_widget_size = 0;

    if (bin->child && GTK_WIDGET_VISIBLE (bin->child))
        gtk_widget_get_child_requisition (bin->child, &child_requisition);

    if (paned->priv->handle_visible)
        clamp_handle_size (paned);

    if (paned->priv->button_box_visible)
        clamp_button_box_size (paned);

    clamp_child_requisition (paned, &child_requisition);

    if (paned->priv->pane_widget_visible)
    {
        clamp_pane_widget_size (paned, &child_requisition);
        paned->priv->position = paned->priv->pane_widget_size;
    }

    if (GTK_WIDGET_REALIZED (widget))
        gdk_window_move_resize (paned->priv->bin_window,
                                allocation->x,
                                allocation->y,
                                allocation->width,
                                allocation->height);

    if (paned->priv->button_box_visible)
    {
        get_button_box_allocation (paned, &child_allocation);
        gtk_widget_size_allocate (paned->button_box, &child_allocation);
    }

    if (bin->child)
    {
        get_bin_child_allocation (paned, &child_allocation);
        gtk_widget_size_allocate (bin->child, &child_allocation);
    }

    if (GTK_WIDGET_REALIZED (widget))
    {
        GdkRectangle rect;

        if (paned->priv->pane_widget_visible)
        {
            get_pane_window_rect (paned, &rect);
            gdk_window_move_resize (paned->priv->pane_window,
                                    rect.x, rect.y,
                                    rect.width, rect.height);
        }

        if (paned->priv->handle_visible)
        {
            get_handle_window_rect (paned, &rect);
            gdk_window_move_resize (paned->priv->handle_window,
                                    rect.x, rect.y,
                                    rect.width, rect.height);
        }
    }

    if (paned->priv->pane_widget_visible)
    {
        get_pane_widget_allocation (paned, &child_allocation);
        _moo_pane_size_allocate (paned->priv->current_pane, &child_allocation);
    }
}


static void
moo_paned_map (GtkWidget *widget)
{
    MooPaned *paned = MOO_PANED (widget);

    gdk_window_show (paned->priv->bin_window);

    GTK_WIDGET_CLASS(moo_paned_parent_class)->map (widget);

    if (paned->priv->handle_visible)
    {
        gdk_window_show (paned->priv->pane_window);
        gdk_window_show (paned->priv->handle_window);
    }
}


static void
moo_paned_unmap (GtkWidget *widget)
{
    MooPaned *paned = MOO_PANED (widget);

    if (paned->priv->handle_window)
        gdk_window_hide (paned->priv->handle_window);
    if (paned->priv->pane_window)
        gdk_window_hide (paned->priv->pane_window);
    if (paned->priv->bin_window)
        gdk_window_hide (paned->priv->bin_window);

    GTK_WIDGET_CLASS(moo_paned_parent_class)->unmap (widget);
}


static void
moo_paned_forall (GtkContainer   *container,
                  gboolean        include_internals,
                  GtkCallback     callback,
                  gpointer        callback_data)
{
    MooPaned *paned = MOO_PANED (container);
    GtkBin *bin = GTK_BIN (container);
    GSList *l;

    if (bin->child)
        callback (bin->child, callback_data);

    if (include_internals)
    {
        callback (paned->button_box, callback_data);

        for (l = paned->priv->panes; l != NULL; l = l->next)
            callback (_moo_pane_get_frame (l->data), callback_data);
    }
}


static gboolean
moo_paned_expose (GtkWidget      *widget,
                  GdkEventExpose *event)
{
    MooPaned *paned = MOO_PANED (widget);

    if (paned->priv->button_box_visible)
        gtk_container_propagate_expose (GTK_CONTAINER (paned),
                                        paned->button_box, event);

    if (GTK_BIN(paned)->child && GTK_WIDGET_DRAWABLE (GTK_BIN(paned)->child))
        gtk_container_propagate_expose (GTK_CONTAINER (paned),
                                        GTK_BIN(paned)->child,
                                        event);

    if (paned->priv->pane_widget_visible)
        gtk_container_propagate_expose (GTK_CONTAINER (paned),
                                        _moo_pane_get_frame (paned->priv->current_pane),
                                        event);

    if (paned->priv->handle_visible && event->window == paned->priv->handle_window)
        draw_handle (paned, event);

    if (paned->priv->button_box_visible && !paned->priv->pane_widget_visible &&
        paned->priv->border_size && event->window == paned->priv->bin_window)
            draw_border (paned, event);

    return TRUE;
}


#if 0
/* TODO */
static GdkEventExpose *clip_bin_child_event (MooPaned       *paned,
                                             GdkEventExpose *event)
{
    GtkAllocation child_alloc;
    GdkRegion *child_rect;
    GdkEventExpose *child_event;

    get_bin_child_allocation (paned, &child_alloc);
    child_rect = gdk_region_rectangle ((GdkRectangle*) &child_alloc);

    child_event = (GdkEventExpose*) gdk_event_copy ((GdkEvent*) event);
    gdk_region_intersect (child_event->region, child_rect);
    gdk_region_get_clipbox (child_event->region, &child_event->area);

    gdk_region_destroy (child_rect);
    return child_event;
}
#endif


static void
moo_paned_add (GtkContainer   *container,
               GtkWidget      *child)
{
    GtkBin *bin = GTK_BIN (container);

    g_return_if_fail (GTK_IS_WIDGET (child));

    if (bin->child != NULL)
    {
        g_warning ("Attempting to add a widget with type %s to a %s, "
                   "but as a GtkBin subclass a %s can only contain one widget at a time; "
                   "it already contains a widget of type %s",
        g_type_name (G_OBJECT_TYPE (child)),
        g_type_name (G_OBJECT_TYPE (bin)),
        g_type_name (G_OBJECT_TYPE (bin)),
        g_type_name (G_OBJECT_TYPE (bin->child)));
        return;
    }

    gtk_widget_set_parent_window (child, MOO_PANED(container)->priv->bin_window);
    gtk_widget_set_parent (child, GTK_WIDGET (bin));
    bin->child = child;
}


static void
moo_paned_remove (GtkContainer   *container,
                  GtkWidget      *widget)
{
    MooPaned *paned = MOO_PANED (container);

    g_return_if_fail (widget == GTK_BIN(paned)->child);

    GTK_CONTAINER_CLASS(moo_paned_parent_class)->remove (container, widget);
}


static void
draw_handle (MooPaned       *paned,
             GdkEventExpose *event)
{
    GtkWidget *widget = GTK_WIDGET (paned);
    GtkStateType state;
    GdkRectangle area = {0, 0, 0, 0};
    GtkOrientation orientation = GTK_ORIENTATION_VERTICAL;
    int shadow_size = 0;

    switch (paned->priv->pane_position)
    {
        case MOO_PANE_POS_LEFT:
        case MOO_PANE_POS_RIGHT:
            shadow_size = widget->style->xthickness;
            area.width = paned->priv->handle_size;
            area.height = widget->allocation.height;
            if (area.width <= 3*shadow_size)
                shadow_size = 0;
            area.x += shadow_size;
            area.width -= shadow_size;
            orientation = GTK_ORIENTATION_VERTICAL;
            break;
        case MOO_PANE_POS_TOP:
        case MOO_PANE_POS_BOTTOM:
            shadow_size = widget->style->ythickness;
            area.width = widget->allocation.width;
            area.height = paned->priv->handle_size;
            if (area.height <= 3 * shadow_size)
                shadow_size = 0;
            area.y += shadow_size;
            area.height -= shadow_size;
            orientation = GTK_ORIENTATION_HORIZONTAL;
            break;
    }

    if (gtk_widget_is_focus (widget))
        state = GTK_STATE_SELECTED;
    else if (paned->priv->handle_prelit)
        state = GTK_STATE_PRELIGHT;
    else
        state = GTK_WIDGET_STATE (widget);

    gtk_paint_handle (widget->style,
                      paned->priv->handle_window,
                      state,
                      GTK_SHADOW_NONE,
                      &event->area,
                      widget,
                      "paned",
                      area.x, area.y, area.width, area.height,
                      orientation);

    if (shadow_size)
    {
        if (orientation == GTK_ORIENTATION_VERTICAL)
        {
            area.x -= shadow_size;
            area.width = shadow_size;

            gtk_paint_vline (widget->style,
                             paned->priv->handle_window,
                             GTK_STATE_NORMAL,
                             &event->area,
                             widget,
                             "moo-paned",
                             area.y,
                             area.y + area.height,
                             area.x);

            area.x = paned->priv->handle_size - shadow_size;

            gtk_paint_vline (widget->style,
                             paned->priv->handle_window,
                             GTK_STATE_NORMAL,
                             &event->area,
                             widget,
                             "moo-paned",
                             area.y,
                             area.y + area.height,
                             area.x);
        }
        else
        {
            area.y -= shadow_size;
            area.height = shadow_size;

            gtk_paint_hline (widget->style,
                             paned->priv->handle_window,
                             GTK_STATE_NORMAL,
                             &event->area,
                             widget,
                             "moo-paned",
                             area.x,
                             area.x + area.width,
                             area.y);

            area.y = paned->priv->handle_size - shadow_size;

            gtk_paint_hline (widget->style,
                             paned->priv->handle_window,
                             GTK_STATE_NORMAL,
                             &event->area,
                             widget,
                             "moo-paned",
                             area.x,
                             area.x + area.width,
                             area.y);
        }
    }
}


static void
draw_border (MooPaned       *paned,
             GdkEventExpose *event)
{
    GdkRectangle rect;
    GtkWidget *widget = GTK_WIDGET (paned);

    rect.x = paned->priv->button_box_size;
    rect.y = paned->priv->button_box_size;

    switch (paned->priv->pane_position)
    {
        case MOO_PANE_POS_RIGHT:
            rect.x = widget->allocation.width -
                        paned->priv->button_box_size -
                        paned->priv->border_size;
        case MOO_PANE_POS_LEFT:
            rect.y = 0;
            rect.height = widget->allocation.height;
            rect.width = paned->priv->border_size;

            gtk_paint_vline (widget->style,
                             paned->priv->bin_window,
                             GTK_STATE_NORMAL,
                             &event->area,
                             widget,
                             "moo-paned",
                             rect.y,
                             rect.y + rect.height,
                             rect.x);
            break;

        case MOO_PANE_POS_BOTTOM:
            rect.y = widget->allocation.height -
                    paned->priv->button_box_size -
                    paned->priv->border_size;
        case MOO_PANE_POS_TOP:
            rect.x = 0;
            rect.width = widget->allocation.width;
            rect.height = paned->priv->border_size;

            gtk_paint_hline (widget->style,
                             paned->priv->bin_window,
                             GTK_STATE_NORMAL,
                             &event->area,
                             widget,
                             "moo-paned",
                             rect.x,
                             rect.x + rect.width,
                             rect.y);
            break;
    }
}


void
moo_paned_set_sticky_pane (MooPaned   *paned,
                           gboolean    sticky)
{
    g_return_if_fail (MOO_IS_PANED (paned));

    if (paned->priv->sticky != sticky)
    {
        paned->priv->sticky = sticky;

        if (GTK_WIDGET_REALIZED (paned))
            gtk_widget_queue_resize (GTK_WIDGET (paned));

        g_object_notify (G_OBJECT (paned), "sticky-pane");
    }
}


MooPane *
moo_paned_get_nth_pane (MooPaned *paned,
                        guint     n)
{
    g_return_val_if_fail (MOO_IS_PANED (paned), NULL);
    return get_nth_pane (paned, n);
}


MooPane *
moo_paned_get_pane (MooPaned  *paned,
                    GtkWidget *widget)
{
    MooPane *pane;

    g_return_val_if_fail (MOO_IS_PANED (paned), NULL);
    g_return_val_if_fail (GTK_IS_WIDGET (widget), NULL);

    pane = g_object_get_data (G_OBJECT (widget), "moo-pane");

    if (pane && _moo_pane_get_parent (pane) == paned)
        return pane;
    else
        return NULL;
}


int
moo_paned_get_pane_num (MooPaned  *paned,
                        GtkWidget *widget)
{
    MooPane *pane;

    g_return_val_if_fail (MOO_IS_PANED (paned), -1);
    g_return_val_if_fail (GTK_IS_WIDGET (widget), -1);

    pane = g_object_get_data (G_OBJECT (widget), "moo-pane");

    if (pane)
        return pane_index (paned, pane);
    else
        return -1;
}


static gboolean
moo_paned_motion (GtkWidget      *widget,
                  G_GNUC_UNUSED GdkEventMotion *event)
{
    MooPaned *paned = MOO_PANED (widget);

    if (paned->priv->in_drag)
    {
        int size = 0;
        GtkRequisition requisition;

        _moo_pane_get_size_request (paned->priv->current_pane, &requisition);

        switch (paned->priv->pane_position)
        {
            case MOO_PANE_POS_LEFT:
            case MOO_PANE_POS_RIGHT:
                gdk_window_get_pointer (paned->priv->bin_window, &size, NULL, NULL);

                if (paned->priv->pane_position == MOO_PANE_POS_RIGHT)
                    size = widget->allocation.width - size;

                size -= (paned->priv->drag_start + paned->priv->button_box_size);
                size = CLAMP (size, requisition.width,
                              widget->allocation.width - paned->priv->button_box_size -
                                      paned->priv->handle_size);
                break;

            case MOO_PANE_POS_TOP:
            case MOO_PANE_POS_BOTTOM:
                gdk_window_get_pointer (paned->priv->bin_window, NULL, &size, NULL);

                if (paned->priv->pane_position == MOO_PANE_POS_BOTTOM)
                    size = widget->allocation.height - size;

                size -= (paned->priv->drag_start + paned->priv->button_box_size);
                size = CLAMP (size, requisition.height,
                              widget->allocation.height - paned->priv->button_box_size -
                                      paned->priv->handle_size);
                break;
        }

        if (size != paned->priv->pane_widget_size)
            moo_paned_set_pane_size (paned, size);
    }

    return FALSE;
}


static void
get_handle_rect (MooPaned     *paned,
                 GdkRectangle *rect)
{
    rect->x = rect->y = 0;

    switch (paned->priv->pane_position)
    {
        case MOO_PANE_POS_LEFT:
        case MOO_PANE_POS_RIGHT:
            rect->width = paned->priv->handle_size;
            rect->height = GTK_WIDGET(paned)->allocation.height;
            break;
        case MOO_PANE_POS_TOP:
        case MOO_PANE_POS_BOTTOM:
            rect->height = paned->priv->handle_size;
            rect->width = GTK_WIDGET(paned)->allocation.width;
            break;
    }
}


static gboolean
moo_paned_enter (GtkWidget      *widget,
                 GdkEventCrossing *event)
{
    MooPaned *paned = MOO_PANED (widget);
    GdkRectangle rect;

    if (event->window == paned->priv->handle_window &&
        !paned->priv->in_drag)
    {
        paned->priv->handle_prelit = TRUE;
        get_handle_rect (paned, &rect);
        gdk_window_invalidate_rect (paned->priv->handle_window,
                                         &rect, FALSE);
        return TRUE;
    }

    return FALSE;
}


static gboolean moo_paned_leave     (GtkWidget      *widget,
                                     GdkEventCrossing *event)
{
    MooPaned *paned = MOO_PANED (widget);
    GdkRectangle rect;

    if (event->window == paned->priv->handle_window &&
        !paned->priv->in_drag)
    {
        paned->priv->handle_prelit = FALSE;
        get_handle_rect (paned, &rect);
        gdk_window_invalidate_rect (paned->priv->handle_window,
                                         &rect, FALSE);
        return TRUE;
    }

    return FALSE;
}


static gboolean
moo_paned_button_press (GtkWidget      *widget,
                        GdkEventButton *event)
{
    MooPaned *paned = MOO_PANED (widget);

    if (!paned->priv->in_drag &&
         (event->window == paned->priv->handle_window) &&
         (event->button == 1) &&
         paned->priv->pane_widget_visible)
    {
        paned->priv->in_drag = TRUE;

        /* This is copied from gtkpaned.c */
        gdk_pointer_grab (paned->priv->handle_window, FALSE,
                          GDK_POINTER_MOTION_HINT_MASK
                                  | GDK_BUTTON1_MOTION_MASK
                                  | GDK_BUTTON_RELEASE_MASK
                                  | GDK_ENTER_NOTIFY_MASK
                                  | GDK_LEAVE_NOTIFY_MASK,
                          NULL, NULL,
                          event->time);

        switch (paned->priv->pane_position)
        {
            case MOO_PANE_POS_LEFT:
            case MOO_PANE_POS_RIGHT:
                paned->priv->drag_start = event->x;
                break;
            case MOO_PANE_POS_TOP:
            case MOO_PANE_POS_BOTTOM:
                paned->priv->drag_start = event->y;
                break;
        }

        return TRUE;
    }

    return FALSE;
}


static gboolean
moo_paned_button_release (GtkWidget      *widget,
                          GdkEventButton *event)
{
    MooPaned *paned = MOO_PANED (widget);

    if (paned->priv->in_drag && (event->button == 1))
    {
        paned->priv->in_drag = FALSE;
        paned->priv->drag_start = -1;
        gdk_display_pointer_ungrab (gtk_widget_get_display (widget),
                                    event->time);
        return TRUE;
    }

    return FALSE;
}


int
moo_paned_get_pane_size (MooPaned   *paned)
{
    g_return_val_if_fail (MOO_IS_PANED (paned), 0);
    return paned->priv->position;
}


int
moo_paned_get_button_box_size (MooPaned *paned)
{
    g_return_val_if_fail (MOO_IS_PANED (paned), 0);
    return paned->priv->button_box_size;
}


static void
moo_paned_set_pane_size_real (MooPaned   *paned,
                              int         size)
{
    GtkWidget *widget;
    GdkRectangle rect;

    g_return_if_fail (MOO_IS_PANED (paned));

    if (!GTK_WIDGET_REALIZED (paned))
    {
        paned->priv->position = size;
        return;
    }

    widget = GTK_WIDGET (paned);

    switch (paned->priv->pane_position)
    {
        case MOO_PANE_POS_LEFT:
        case MOO_PANE_POS_RIGHT:
            size = CLAMP (size, 0,
                          widget->allocation.width - paned->priv->button_box_size -
                                  paned->priv->handle_size);
            break;
        case MOO_PANE_POS_TOP:
        case MOO_PANE_POS_BOTTOM:
            size = CLAMP (size, 0,
                          widget->allocation.height - paned->priv->button_box_size -
                                  paned->priv->handle_size);
            break;
    }

    if (size == paned->priv->position)
        return;

    paned->priv->position = size;

    if (!paned->priv->pane_widget_visible)
        return;

    /* button box redrawing is too slow */
    if (!paned->priv->button_box_visible)
    {
        gtk_widget_queue_resize (widget);
        return;
    }

    rect.x = widget->allocation.x;
    rect.y = widget->allocation.y;
    rect.width = widget->allocation.width;
    rect.height = widget->allocation.height;

    switch (paned->priv->pane_position)
    {
        case MOO_PANE_POS_LEFT:
            rect.x += paned->priv->button_box_size;
            rect.width -= paned->priv->button_box_size;
            break;
        case MOO_PANE_POS_RIGHT:
            rect.width -= paned->priv->button_box_size;
            break;
        case MOO_PANE_POS_TOP:
            rect.y += paned->priv->button_box_size;
            rect.height -= paned->priv->button_box_size;
            break;
        case MOO_PANE_POS_BOTTOM:
            rect.height -= paned->priv->button_box_size;
            break;
    }

    gtk_widget_queue_resize_no_redraw (widget);
}


void
moo_paned_set_pane_size (MooPaned       *paned,
                         int             size)
{
    g_return_if_fail (MOO_IS_PANED (paned));
    g_signal_emit (paned, paned_signals[PANED_SET_PANE_SIZE], 0, size);
}


static void
button_box_visible_notify (MooPaned *paned)
{
    gboolean visible = GTK_WIDGET_VISIBLE (paned->button_box);

    if (paned->priv->button_box_visible == visible)
        return;

    if (paned->priv->panes)
        paned->priv->button_box_visible = visible;

    if (GTK_WIDGET_REALIZED (paned))
        gtk_widget_queue_resize (GTK_WIDGET (paned));
}


void
_moo_paned_insert_pane (MooPaned *paned,
                        MooPane  *pane,
                        int       position)
{
    GtkWidget *handle;

    g_return_if_fail (MOO_IS_PANED (paned));
    g_return_if_fail (MOO_IS_PANE (pane));
    g_return_if_fail (_moo_pane_get_parent (pane) == NULL);

    g_object_ref (pane);
    _moo_pane_set_parent (pane, paned, paned->priv->pane_window);

    if (position < 0 || position > (int) moo_paned_n_panes (paned))
        position = moo_paned_n_panes (paned);

    gtk_container_add_with_properties (GTK_CONTAINER (paned->button_box),
                                       _moo_pane_get_button (pane),
                                       "expand", FALSE,
                                       "fill", FALSE,
                                       "pack-type", GTK_PACK_START,
                                       "position", position,
                                       NULL);

    paned->priv->panes = g_slist_insert (paned->priv->panes,
                                         pane, position);

    g_signal_connect (_moo_pane_get_button (pane), "toggled",
                      G_CALLBACK (pane_button_toggled), paned);

    handle = _moo_pane_get_handle (pane);
    g_signal_connect (handle, "button-press-event",
                      G_CALLBACK (handle_button_press), paned);
    g_signal_connect (handle, "button-release-event",
                      G_CALLBACK (handle_button_release), paned);
    g_signal_connect (handle, "motion-notify-event",
                      G_CALLBACK (handle_motion), paned);
    g_signal_connect (handle, "expose-event",
                      G_CALLBACK (handle_expose), paned);

    gtk_widget_show (paned->button_box);
    paned->priv->button_box_visible = TRUE;

    if (GTK_WIDGET_VISIBLE (paned))
        gtk_widget_queue_resize (GTK_WIDGET (paned));
}


MooPane *
moo_paned_insert_pane (MooPaned       *paned,
                       GtkWidget      *pane_widget,
                       MooPaneLabel   *pane_label,
                       int             position)
{
    MooPane *pane;

    g_return_val_if_fail (MOO_IS_PANED (paned), NULL);
    g_return_val_if_fail (GTK_IS_WIDGET (pane_widget), NULL);
    g_return_val_if_fail (pane_label != NULL, NULL);
    g_return_val_if_fail (pane_widget->parent == NULL, NULL);

    pane = _moo_pane_new (pane_widget, pane_label);
    _moo_paned_insert_pane (paned, pane, position);
    MOO_OBJECT_REF_SINK (pane);

    return pane;
}


gboolean
moo_paned_remove_pane (MooPaned  *paned,
                       GtkWidget *pane_widget)
{
    MooPane *pane;
    int index;

    g_return_val_if_fail (MOO_IS_PANED (paned), FALSE);
    g_return_val_if_fail (GTK_IS_WIDGET (pane_widget), FALSE);

    pane = g_object_get_data (G_OBJECT (pane_widget), "moo-pane");
    g_return_val_if_fail (pane != NULL, FALSE);
    g_return_val_if_fail (g_slist_find (paned->priv->panes, pane) != NULL, FALSE);

    if (paned->priv->current_pane == pane)
    {
        index = pane_index (paned, pane);
        if (index > 0)
            index = index - 1;
        else if (moo_paned_n_panes (paned) > 1)
            index = 1;
        else
            index = -1;

        if (index >= 0)
            moo_paned_open_pane (paned, get_nth_pane (paned, index));
        else
            moo_paned_hide_pane (paned);
    }

    if (_moo_pane_get_detached (pane))
    {
        _moo_pane_freeze_params (pane);
        moo_paned_attach_pane (paned, pane);
        _moo_pane_thaw_params (pane);
    }

    g_signal_handlers_disconnect_by_func (_moo_pane_get_button (pane),
                                          (gpointer) pane_button_toggled,
                                          paned);

    g_signal_handlers_disconnect_by_func (_moo_pane_get_handle (pane),
                                          (gpointer) handle_button_press,
                                          paned);
    g_signal_handlers_disconnect_by_func (_moo_pane_get_handle (pane),
                                          (gpointer) handle_button_release,
                                          paned);
    g_signal_handlers_disconnect_by_func (_moo_pane_get_handle (pane),
                                          (gpointer) handle_motion,
                                          paned);
    g_signal_handlers_disconnect_by_func (_moo_pane_get_handle (pane),
                                          (gpointer) handle_expose,
                                          paned);
    g_signal_handlers_disconnect_by_func (_moo_pane_get_handle (pane),
                                          (gpointer) handle_realize,
                                          paned);

    gtk_container_remove (GTK_CONTAINER (paned->button_box), _moo_pane_get_button (pane));
    paned->priv->panes = g_slist_remove (paned->priv->panes, pane);

    _moo_pane_unparent (pane);
    g_object_unref (pane);

    if (!moo_paned_n_panes (paned))
    {
        paned->priv->handle_visible = FALSE;
        paned->priv->handle_size = 0;
        if (paned->priv->pane_window)
            gdk_window_hide (paned->priv->pane_window);
        gtk_widget_hide (paned->button_box);
        paned->priv->button_box_visible = FALSE;
    }

    gtk_widget_queue_resize (GTK_WIDGET (paned));

    return TRUE;
}


guint
moo_paned_n_panes (MooPaned *paned)
{
    g_return_val_if_fail (MOO_IS_PANED (paned), 0);
    return g_slist_length (paned->priv->panes);
}


static GtkWidget *
find_focus (GtkWidget *widget)
{
    GtkWidget *focus_child, *window;

    if (!widget)
        return NULL;

    window = gtk_widget_get_toplevel (widget);

    if (!GTK_IS_WINDOW (window))
        return NULL;

    focus_child = gtk_window_get_focus (GTK_WINDOW (window));

    if (focus_child && gtk_widget_is_ancestor (focus_child, widget))
        return focus_child;
    else
        return NULL;
}


static GtkWidget *
find_focus_child (MooPaned *paned)
{
    return find_focus (GTK_BIN(paned)->child);
}


static void
moo_paned_set_focus_child (GtkContainer *container,
                           GtkWidget    *widget)
{
    MooPaned *paned = MOO_PANED (container);
    FocusPosition new_focus = FOCUS_NONE;
    MooPane *new_focus_pane = NULL;
    MooPane *old_focus_pane = paned->priv->focus_pane;
    GSList *l;

    if (widget)
    {
        if (widget == GTK_BIN(paned)->child)
            new_focus = FOCUS_CHILD;
        else if (widget == paned->button_box)
            new_focus = FOCUS_BUTTON;

        if (!new_focus)
        {
            for (l = paned->priv->panes; l != NULL; l = l->next)
            {
                MooPane *pane = l->data;

                if (widget == _moo_pane_get_frame (pane))
                {
                    new_focus_pane = pane;
                    new_focus = FOCUS_PANE;
                    break;
                }
            }
        }

        if (!new_focus)
        {
            g_critical ("%s: oops", G_STRLOC);
            GTK_CONTAINER_CLASS(moo_paned_parent_class)->set_focus_child (container, widget);
            paned->priv->focus = FOCUS_NONE;
            paned->priv->focus_pane = NULL;
            g_return_if_reached ();
        }
    }

    if (new_focus != FOCUS_BUTTON)
        paned->priv->button_real_focus = FALSE;

    switch (paned->priv->focus)
    {
        case FOCUS_NONE:
        case FOCUS_BUTTON:
            break;

        case FOCUS_CHILD:
            if (new_focus != FOCUS_CHILD)
            {
                if (paned->priv->focus_child)
                    g_object_remove_weak_pointer (paned->priv->focus_child,
                                                  &paned->priv->focus_child);

                paned->priv->focus_child = find_focus_child (paned);

                if (paned->priv->focus_child)
                    g_object_add_weak_pointer (paned->priv->focus_child,
                                               &paned->priv->focus_child);
            }
            break;

        case FOCUS_PANE:
            g_assert (old_focus_pane != NULL);
            if (new_focus_pane != old_focus_pane)
                _moo_pane_update_focus_child (old_focus_pane);
            break;
    }

    GTK_CONTAINER_CLASS(moo_paned_parent_class)->set_focus_child (container, widget);

    paned->priv->focus = new_focus;
    paned->priv->focus_pane = new_focus_pane;

    if (new_focus == FOCUS_CHILD &&
        paned->priv->close_on_child_focus &&
        !paned->priv->sticky)
    {
        paned->priv->dont_move_focus = TRUE;
        moo_paned_hide_pane (paned);
        paned->priv->dont_move_focus = FALSE;
    }
}


static gboolean
focus_to_child (MooPaned         *paned,
                GtkDirectionType  direction)
{
    return GTK_BIN(paned)->child &&
            gtk_widget_child_focus (GTK_BIN(paned)->child, direction);
}


static gboolean
focus_to_pane (MooPaned         *paned,
               GtkDirectionType  direction)
{
    MooPane *pane = paned->priv->current_pane;

    if (!pane)
        return FALSE;
    else if (find_focus (_moo_pane_get_frame (pane)))
        return gtk_widget_child_focus (_moo_pane_get_frame (pane), direction);
    else
        return gtk_widget_child_focus (moo_pane_get_child (pane), direction) ||
                gtk_widget_child_focus (_moo_pane_get_frame (pane), direction);
}


static gboolean
focus_to_button (MooPaned         *paned,
                 GtkDirectionType  direction)
{
    if (gtk_widget_child_focus (paned->button_box, direction))
    {
        paned->priv->button_real_focus = TRUE;
        return TRUE;
    }
    else
    {
        return FALSE;
    }
}


static gboolean
moo_left_paned_focus (MooPaned         *paned,
                      GtkDirectionType  direction)
{
    switch (paned->priv->focus)
    {
        case FOCUS_NONE:
            switch (direction)
            {
                case GTK_DIR_LEFT:
                case GTK_DIR_UP:
                    return focus_to_child (paned, direction) ||
                            (paned->priv->current_pane && focus_to_pane (paned, direction)) ||
                            focus_to_button (paned, direction);
                case GTK_DIR_RIGHT:
                case GTK_DIR_DOWN:
                    return focus_to_button (paned, direction) ||
                            focus_to_child (paned, direction);
                default:
                    g_return_val_if_reached (FALSE);
            }

        case FOCUS_CHILD:
            if (focus_to_child (paned, direction))
                return TRUE;

            switch (direction)
            {
                case GTK_DIR_LEFT:
                    return (paned->priv->current_pane && focus_to_pane (paned, direction)) ||
                            focus_to_button (paned, direction);
                default:
                    return FALSE;
            }

        case FOCUS_PANE:
            if (focus_to_pane (paned, direction))
                return TRUE;

            switch (direction)
            {
                case GTK_DIR_LEFT:
                    return focus_to_button (paned, direction);
                case GTK_DIR_RIGHT:
                    return focus_to_child (paned, direction);
                default:
                    return FALSE;
            }

        case FOCUS_BUTTON:
            if (focus_to_button (paned, direction))
                return TRUE;

            switch (direction)
            {
                case GTK_DIR_RIGHT:
                    return focus_to_pane (paned, direction) ||
                            focus_to_child (paned, direction);
                default:
                    return FALSE;
            }
    }

    g_return_val_if_reached (FALSE);
}


static gboolean
moo_left_paned_tab_focus (MooPaned         *paned,
                          gboolean          forward,
                          GtkDirectionType  direction)
{
    if (forward)
    {
        switch (paned->priv->focus)
        {
            case FOCUS_NONE:
                return focus_to_button (paned, direction) ||
                        focus_to_child (paned, direction);
            case FOCUS_CHILD:
                return focus_to_child (paned, direction);
            case FOCUS_PANE:
                return focus_to_pane (paned, direction) ||
                        focus_to_child (paned, direction);
            case FOCUS_BUTTON:
                return focus_to_button (paned, direction) ||
                        focus_to_pane (paned, direction) ||
                        focus_to_child (paned, direction);
        }
    }
    else
    {
        switch (paned->priv->focus)
        {
            case FOCUS_NONE:
            case FOCUS_CHILD:
                return focus_to_child (paned, direction) ||
                        focus_to_pane (paned, direction) ||
                        focus_to_button (paned, direction);
            case FOCUS_PANE:
                return focus_to_pane (paned, direction) ||
                        focus_to_button (paned, direction);
            case FOCUS_BUTTON:
                return focus_to_button (paned, direction);
        }
    }

    g_return_val_if_reached (FALSE);
}


static gboolean
moo_top_paned_tab_focus (MooPaned         *paned,
                         GtkDirectionType  direction)
{
    switch (paned->priv->focus)
    {
        case FOCUS_NONE:
            return focus_to_button (paned, direction) ||
                    focus_to_child (paned, direction);
        case FOCUS_BUTTON:
            return focus_to_button (paned, direction) ||
                    focus_to_pane (paned, direction) ||
                    focus_to_child (paned, direction);
        case FOCUS_PANE:
            return focus_to_pane (paned, direction) ||
                    focus_to_child (paned, direction);
        case FOCUS_CHILD:
            return focus_to_child (paned, direction);
    }

    g_return_val_if_reached (FALSE);
}


static gboolean
moo_paned_focus (GtkWidget       *widget,
                 GtkDirectionType direction)
{
    MooPaned *paned = MOO_PANED (widget);
    gboolean invert = FALSE;
    gboolean flip = FALSE;

    paned->priv->button_real_focus = FALSE;

    if (direction == GTK_DIR_TAB_FORWARD ||
        direction == GTK_DIR_TAB_BACKWARD)
    {
        switch (paned->priv->pane_position)
        {
            case MOO_PANE_POS_RIGHT:
                return moo_left_paned_tab_focus (paned, direction != GTK_DIR_TAB_FORWARD,
                                                 direction);
            case MOO_PANE_POS_LEFT:
                return moo_left_paned_tab_focus (paned, direction == GTK_DIR_TAB_FORWARD,
                                                 direction);

            case MOO_PANE_POS_BOTTOM:
            case MOO_PANE_POS_TOP:
                return moo_top_paned_tab_focus (paned, direction);
        }
    }

    switch (paned->priv->pane_position)
    {
        case MOO_PANE_POS_RIGHT:
            invert = TRUE;
            /* fall through */
        case MOO_PANE_POS_LEFT:
            break;

        case MOO_PANE_POS_BOTTOM:
            invert = TRUE;
            /* fall through */
        case MOO_PANE_POS_TOP:
            flip = TRUE;
            break;
    }

    if (invert)
    {
        switch (direction)
        {
            case GTK_DIR_RIGHT:
                direction = GTK_DIR_LEFT;
                break;
            case GTK_DIR_LEFT:
                direction = GTK_DIR_RIGHT;
                break;
            case GTK_DIR_UP:
                direction = GTK_DIR_DOWN;
                break;
            case GTK_DIR_DOWN:
                direction = GTK_DIR_UP;
                break;
            default:
                g_return_val_if_reached (FALSE);
        }
    }

    if (flip)
    {
        switch (direction)
        {
            case GTK_DIR_RIGHT:
                direction = GTK_DIR_DOWN;
                break;
            case GTK_DIR_DOWN:
                direction = GTK_DIR_RIGHT;
                break;
            case GTK_DIR_LEFT:
                direction = GTK_DIR_UP;
                break;
            case GTK_DIR_UP:
                direction = GTK_DIR_LEFT;
                break;
            default:
                g_return_val_if_reached (FALSE);
        }
    }

    return moo_left_paned_focus (paned, direction);
}


void
moo_paned_present_pane (MooPaned *paned,
                        MooPane  *pane)
{
    g_return_if_fail (MOO_IS_PANED (paned));
    g_return_if_fail (MOO_IS_PANE (pane));
    g_return_if_fail (_moo_pane_get_parent (pane) == paned);

    if (paned->priv->current_pane == pane)
    {
        paned->priv->dont_move_focus = FALSE;

        if (!find_focus (moo_pane_get_child (pane)))
        {
            if (_moo_pane_get_focus_child (pane))
            {
                gtk_widget_grab_focus (_moo_pane_get_focus_child (pane));
            }
            else if (!gtk_widget_child_focus (moo_pane_get_child (pane), GTK_DIR_TAB_FORWARD))
            {
                paned->priv->button_real_focus = FALSE;
                gtk_widget_grab_focus (_moo_pane_get_button (pane));
            }
        }

        return;
    }
    else if (_moo_pane_get_detached (pane))
    {
        gtk_window_present (GTK_WINDOW (_moo_pane_get_window (pane)));
    }
    else
    {
        moo_paned_open_pane (paned, pane);
    }
}


static void
moo_paned_open_pane_real (MooPaned *paned,
                          guint     index)
{
    MooPane *pane;
    FocusPosition old_focus;

    g_return_if_fail (index < moo_paned_n_panes (paned));

    pane = get_nth_pane (paned, index);
    g_return_if_fail (pane != NULL);

    if (paned->priv->current_pane == pane)
        return;

    old_focus = paned->priv->focus;

    if (paned->priv->current_pane)
    {
        MooPane *old_pane = paned->priv->current_pane;
        paned->priv->current_pane = NULL;
        gtk_toggle_button_set_active (GTK_TOGGLE_BUTTON (_moo_pane_get_button (old_pane)), FALSE);
        gtk_widget_hide (_moo_pane_get_frame (old_pane));
    }

    if (GTK_WIDGET_MAPPED (paned))
    {
        gdk_window_show (paned->priv->pane_window);
        gdk_window_show (paned->priv->handle_window);
    }

    gtk_widget_set_parent_window (_moo_pane_get_frame (pane), paned->priv->pane_window);

    paned->priv->current_pane = pane;
    gtk_widget_show (_moo_pane_get_frame (pane));

    gtk_toggle_button_set_active (GTK_TOGGLE_BUTTON (_moo_pane_get_button (pane)), TRUE);

    if (_moo_pane_get_detached (pane))
        moo_paned_attach_pane (paned, pane);

    paned->priv->handle_visible = TRUE;
    paned->priv->pane_widget_visible = TRUE;
    if (paned->priv->position > 0)
        paned->priv->pane_widget_size = paned->priv->position;

    /* XXX it's wrong, it should look if button was clicked */
    if (!paned->priv->dont_move_focus &&
        (old_focus != FOCUS_BUTTON || !paned->priv->button_real_focus))
    {
        if (_moo_pane_get_focus_child (pane))
        {
            gtk_widget_grab_focus (_moo_pane_get_focus_child (pane));
        }
        else if (!gtk_widget_child_focus (moo_pane_get_child (pane), GTK_DIR_TAB_FORWARD))
        {
            paned->priv->button_real_focus = FALSE;
            gtk_widget_grab_focus (_moo_pane_get_button (pane));
        }
    }

    gtk_widget_queue_resize (GTK_WIDGET (paned));
}


/* XXX invalidate space under the pane */
static void
moo_paned_hide_pane_real (MooPaned *paned)
{
    GtkWidget *button;
    FocusPosition old_focus;

    if (!paned->priv->current_pane)
        return;

    button = _moo_pane_get_button (paned->priv->current_pane);
    old_focus = paned->priv->focus;

    gtk_widget_hide (_moo_pane_get_frame (paned->priv->current_pane));

    if (GTK_WIDGET_REALIZED (paned))
    {
        gdk_window_hide (paned->priv->handle_window);
        gdk_window_hide (paned->priv->pane_window);
    }

    paned->priv->current_pane = NULL;
    paned->priv->pane_widget_visible = FALSE;
    paned->priv->handle_visible = FALSE;
    gtk_widget_queue_resize (GTK_WIDGET (paned));

    /* XXX it's wrong, it should look if button was clicked */
    if (!paned->priv->dont_move_focus &&
        old_focus != FOCUS_NONE &&
        (old_focus != FOCUS_BUTTON || !paned->priv->button_real_focus))
    {
        if (paned->priv->focus_child)
        {
            gtk_widget_grab_focus (paned->priv->focus_child);
        }
        else if (!GTK_BIN(paned)->child ||
                  !gtk_widget_child_focus (GTK_BIN(paned)->child, GTK_DIR_TAB_FORWARD))
        {
            if (GTK_WIDGET_VISIBLE (button))
                gtk_widget_grab_focus (button);
        }
        else
        {
            GtkWidget *toplevel = gtk_widget_get_toplevel (GTK_WIDGET (paned));
            gtk_widget_child_focus (toplevel, GTK_DIR_TAB_FORWARD);
        }
    }

    gtk_toggle_button_set_active (GTK_TOGGLE_BUTTON (button), FALSE);
}


static void
pane_button_toggled (GtkToggleButton *button,
                     MooPaned        *paned)
{
    MooPane *pane;

    pane = g_object_get_data (G_OBJECT (button), "moo-pane");
    g_return_if_fail (MOO_IS_PANE (pane));

    if (!gtk_toggle_button_get_active (button))
    {
        if (paned->priv->current_pane == pane)
            moo_paned_hide_pane (paned);
    }
    else if (!paned->priv->current_pane || paned->priv->current_pane != pane)
    {
        moo_paned_open_pane (paned, pane);
    }
}


void
moo_paned_hide_pane (MooPaned *paned)
{
    g_return_if_fail (MOO_IS_PANED (paned));
    moo_paned_hide_pane_real (paned);
}


void
moo_paned_open_pane (MooPaned *paned,
                     MooPane  *pane)
{
    g_return_if_fail (MOO_IS_PANED (paned));
    g_return_if_fail (MOO_IS_PANE (pane));
    g_return_if_fail (_moo_pane_get_parent (pane) == paned);
    moo_paned_open_pane_real (paned, pane_index (paned, pane));
}


static int
pane_index (MooPaned *paned,
            MooPane  *pane)
{
    return g_slist_index (paned->priv->panes, pane);
}


static MooPane *
get_nth_pane (MooPaned *paned,
              guint     index_)
{
    return g_slist_nth_data (paned->priv->panes, index_);
}


MooPane *
moo_paned_get_open_pane (MooPaned *paned)
{
    g_return_val_if_fail (MOO_IS_PANED (paned), NULL);
    return paned->priv->current_pane;
}


gboolean
moo_paned_is_open (MooPaned *paned)
{
    g_return_val_if_fail (MOO_IS_PANED (paned), FALSE);
    return paned->priv->current_pane != NULL;
}


GType
moo_pane_position_get_type (void)
{
    static GType type = 0;

    if (G_UNLIKELY (!type))
    {
        static const GEnumValue values[] = {
            { MOO_PANE_POS_LEFT, (char*) "MOO_PANE_POS_LEFT", (char*) "left" },
            { MOO_PANE_POS_RIGHT, (char*) "MOO_PANE_POS_RIGHT", (char*) "right" },
            { MOO_PANE_POS_TOP, (char*) "MOO_PANE_POS_TOP", (char*) "top" },
            { MOO_PANE_POS_BOTTOM, (char*) "MOO_PANE_POS_BOTTOM", (char*) "bottom" },
            { 0, NULL, NULL }
        };
        type = g_enum_register_static ("MooPanePosition", values);
    }

    return type;
}


GSList *
moo_paned_list_panes (MooPaned *paned)
{
    g_return_val_if_fail (MOO_IS_PANED (paned), NULL);
    return g_slist_copy (paned->priv->panes);
}


static gboolean
handle_button_press (GtkWidget      *widget,
                     GdkEventButton *event,
                     MooPaned       *paned)
{
#if 1
    GdkCursor *cursor;
#endif

    if (event->button != 1 || event->type != GDK_BUTTON_PRESS)
        return FALSE;

    if (!paned->priv->enable_handle_drag)
        return FALSE;

    g_return_val_if_fail (!paned->priv->handle_in_drag, FALSE);
    g_return_val_if_fail (!paned->priv->handle_button_pressed, FALSE);

    paned->priv->handle_button_pressed = TRUE;
    paned->priv->handle_drag_start_x = event->x;
    paned->priv->handle_drag_start_y = event->y;

#if 1
    cursor = gdk_cursor_new (paned->priv->handle_cursor_type);
    g_return_val_if_fail (cursor != NULL, TRUE);
    gdk_window_set_cursor (widget->window, cursor);
    gdk_cursor_unref (cursor);
#endif

    return TRUE;
}


static gboolean
handle_motion (GtkWidget      *widget,
               GdkEventMotion *event,
               MooPaned       *paned)
{
    MooPane *pane;
    GtkWidget *child;

    if (!paned->priv->handle_button_pressed)
        return FALSE;

    pane = g_object_get_data (G_OBJECT (widget), "moo-pane");
    child = moo_pane_get_child (pane);
    g_return_val_if_fail (child != NULL, FALSE);

    if (!paned->priv->handle_in_drag)
    {
        if (!gtk_drag_check_threshold (widget,
                                       paned->priv->handle_drag_start_x,
                                       paned->priv->handle_drag_start_y,
                                       event->x,
                                       event->y))
            return FALSE;

        paned->priv->handle_in_drag = TRUE;

        g_signal_emit (paned, paned_signals[PANED_HANDLE_DRAG_START], 0, child);
    }

    g_signal_emit (paned, paned_signals[PANED_HANDLE_DRAG_MOTION], 0, child);
    return TRUE;
}


static gboolean
handle_button_release (GtkWidget      *widget,
                       G_GNUC_UNUSED GdkEventButton *event,
                       MooPaned       *paned)
{
    MooPane *pane;
    GtkWidget *child;

    if (paned->priv->handle_button_pressed)
    {
#if 1
        gdk_window_set_cursor (widget->window, NULL);
#endif
        paned->priv->handle_button_pressed = FALSE;
    }

    if (!paned->priv->handle_in_drag)
        return FALSE;

    paned->priv->handle_in_drag = FALSE;

    pane = g_object_get_data (G_OBJECT (widget), "moo-pane");
    child = moo_pane_get_child (pane);
    g_return_val_if_fail (child != NULL, FALSE);

    g_signal_emit (paned, paned_signals[PANED_HANDLE_DRAG_END], 0, child);

    return TRUE;
}


#define HANDLE_HEIGHT 12

static gboolean
handle_expose (GtkWidget      *widget,
               GdkEventExpose *event,
               MooPaned       *paned)
{
    int height;

    if (!paned->priv->enable_handle_drag)
        return FALSE;

    height = MIN (widget->allocation.height, HANDLE_HEIGHT);

    gtk_paint_handle (widget->style,
                      widget->window,
                      widget->state,
                      GTK_SHADOW_ETCHED_IN,
                      &event->area,
                      widget,
                      "moo-pane-handle",
                      0,
                      (widget->allocation.height - height) / 2,
                      widget->allocation.width,
                      height,
                      GTK_ORIENTATION_HORIZONTAL);
    return TRUE;
}


static void
handle_realize (G_GNUC_UNUSED GtkWidget *widget,
                MooPaned  *paned)
{
#if 0
    GdkCursor *cursor;
#endif

    g_return_if_fail (MOO_IS_PANED (paned));
    g_return_if_fail (MOO_PANED(paned)->priv->bin_window != NULL);

    if (!paned->priv->enable_handle_drag)
        return;

#if 0
    cursor = gdk_cursor_new (paned->priv->handle_cursor_type);
    g_return_if_fail (cursor != NULL);
    gdk_window_set_cursor (widget->window, cursor);
    gdk_cursor_unref (cursor);
#endif
}


static void
moo_paned_set_handle_cursor_type (MooPaned     *paned,
                                  GdkCursorType cursor_type,
                                  gboolean      set)
{
//     GSList *l;
    GdkCursor *cursor = NULL;

//     for (l = paned->priv->panes; l != NULL; l = l->next)
//     {
//         MooPane *pane = l->data;
//
//         if (pane->handle && pane->handle->window)
//         {
// #if 0
//             if (set && !cursor)
//             {
//                 cursor = gdk_cursor_new (cursor_type);
//                 g_return_if_fail (cursor != NULL);
//             }
//
//             gdk_window_set_cursor (pane->handle->window, cursor);
// #endif
//         }
//     }

    if (set)
    {
        paned->priv->handle_cursor_type = cursor_type;
        g_object_notify (G_OBJECT (paned), "handle-cursor-type");
    }

    if (cursor)
        gdk_cursor_unref (cursor);
}


MooPaneLabel *
moo_pane_label_new (const char     *icon_stock_id,
                    GdkPixbuf      *pixbuf,
                    const char     *text,
                    const char     *window_title)
{
    MooPaneLabel *label = g_new0 (MooPaneLabel, 1);

    label->icon_stock_id = g_strdup (icon_stock_id);
    label->label = g_strdup (text);
    label->window_title = g_strdup (window_title);

    if (pixbuf)
        label->icon_pixbuf = g_object_ref (pixbuf);

    return label;
}


MooPaneLabel*
moo_pane_label_copy (MooPaneLabel   *label)
{
    MooPaneLabel *copy;

    g_return_val_if_fail (label != NULL, NULL);

    copy = g_new0 (MooPaneLabel, 1);

    copy->icon_stock_id = g_strdup (label->icon_stock_id);
    copy->label = g_strdup (label->label);
    copy->window_title = g_strdup (label->window_title);

    if (label->icon_pixbuf)
        copy->icon_pixbuf = g_object_ref (label->icon_pixbuf);

    return copy;
}


void
moo_pane_label_free (MooPaneLabel *label)
{
    if (label)
    {
        g_free (label->icon_stock_id);
        g_free (label->label);
        g_free (label->window_title);

        if (label->icon_pixbuf)
            g_object_unref (label->icon_pixbuf);

        g_free (label);
    }
}


void
moo_paned_detach_pane (MooPaned *paned,
                       MooPane  *pane)
{
    g_return_if_fail (MOO_IS_PANED (paned));
    g_return_if_fail (MOO_IS_PANE (pane));
    g_return_if_fail (_moo_pane_get_parent (pane) == paned);

    if (_moo_pane_get_detached (pane))
        return;

    if (pane == paned->priv->current_pane)
        moo_paned_hide_pane (paned);

    _moo_pane_detach (pane);
    gtk_widget_queue_resize (GTK_WIDGET (paned));
}


void
moo_paned_attach_pane (MooPaned *paned,
                       MooPane  *pane)
{
    g_return_if_fail (MOO_IS_PANED (paned));
    g_return_if_fail (MOO_IS_PANE (pane));
    g_return_if_fail (_moo_pane_get_parent (pane) == paned);

    if (!_moo_pane_get_detached (pane))
        return;

    _moo_pane_attach (pane);
    gtk_widget_queue_resize (GTK_WIDGET (paned));
}


static void
moo_paned_set_enable_detaching (MooPaned *paned,
                                gboolean  enable)
{
    if (paned->priv->enable_detaching != enable)
    {
        paned->priv->enable_detaching = enable != 0;
        g_object_notify (G_OBJECT (paned), "enable-detaching");
    }
}


void
_moo_paned_attach_pane (MooPaned *paned,
                        MooPane  *pane)
{
    GtkWidget *focus_child;

    g_return_if_fail (MOO_IS_PANED (paned));

    moo_paned_attach_pane (paned, pane);

    paned->priv->dont_move_focus = TRUE;
    moo_paned_open_pane (paned, pane);
    paned->priv->dont_move_focus = TRUE;

    focus_child = _moo_pane_get_focus_child (pane);

    if (focus_child)
        gtk_widget_grab_focus (focus_child);
    else if (!gtk_widget_child_focus (moo_pane_get_child (pane), GTK_DIR_TAB_FORWARD))
        gtk_widget_grab_focus (_moo_pane_get_button (pane));
}


MooPaneParams *
moo_pane_params_new (GdkRectangle *window_position,
                     gboolean      detached,
                     gboolean      maximized,
                     gboolean      keep_on_top)
{
    MooPaneParams *p;

    p = g_new0 (MooPaneParams, 1);
    if (window_position)
        p->window_position = *window_position;
    else
        p->window_position.width = p->window_position.height = -1;
    p->detached = detached != 0;
    p->maximized = maximized != 0;
    p->keep_on_top = keep_on_top != 0;

    return p;
}


MooPaneParams*
moo_pane_params_copy (MooPaneParams *params)
{
    MooPaneParams *copy;

    g_return_val_if_fail (params != NULL, NULL);

    copy = g_new (MooPaneParams, 1);
    memcpy (copy, params, sizeof (MooPaneParams));

    return copy;
}


void
moo_pane_params_free (MooPaneParams *params)
{
    g_free (params);
}


GType
moo_pane_label_get_type (void)
{
    static GType type = 0;

    if (G_UNLIKELY (!type))
        type = g_boxed_type_register_static ("MooPaneLabel",
                                             (GBoxedCopyFunc) moo_pane_label_copy,
                                             (GBoxedFreeFunc) moo_pane_label_free);

    return type;
}


GType
moo_pane_params_get_type (void)
{
    static GType type = 0;

    if (G_UNLIKELY (!type))
        type = g_boxed_type_register_static ("MooPaneParams",
                                             (GBoxedCopyFunc) moo_pane_params_copy,
                                             (GBoxedFreeFunc) moo_pane_params_free);

    return type;
}


static gboolean
moo_paned_key_press (GtkWidget   *widget,
                     GdkEventKey *event)
{
    static int delta = 5;
    int add = 0;
    guint mask = GDK_SHIFT_MASK | GDK_CONTROL_MASK | GDK_MOD1_MASK;
    MooPaned *paned = MOO_PANED (widget);

    if ((event->state & mask) == (GDK_CONTROL_MASK | GDK_MOD1_MASK))
    {
        switch (event->keyval)
        {
            case GDK_Up:
            case GDK_KP_Up:
                if (paned->priv->pane_position == MOO_PANE_POS_TOP)
                    add = -delta;
                else if (paned->priv->pane_position == MOO_PANE_POS_BOTTOM)
                    add = delta;
                break;
            case GDK_Down:
            case GDK_KP_Down:
                if (paned->priv->pane_position == MOO_PANE_POS_TOP)
                    add = delta;
                else if (paned->priv->pane_position == MOO_PANE_POS_BOTTOM)
                    add = -delta;
                break;
            case GDK_Left:
            case GDK_KP_Left:
                if (paned->priv->pane_position == MOO_PANE_POS_LEFT)
                    add = -delta;
                else if (paned->priv->pane_position == MOO_PANE_POS_RIGHT)
                    add = delta;
                break;
            case GDK_Right:
            case GDK_KP_Right:
                if (paned->priv->pane_position == MOO_PANE_POS_LEFT)
                    add = delta;
                else if (paned->priv->pane_position == MOO_PANE_POS_RIGHT)
                    add = -delta;
                break;
        }
    }

    if (!add)
        return GTK_WIDGET_CLASS(moo_paned_parent_class)->key_press_event (widget, event);

    moo_paned_set_pane_size (paned, moo_paned_get_pane_size (paned) + add);
    return TRUE;
}
