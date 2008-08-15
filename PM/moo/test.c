#include "moobigpaned.h"
#include <gtk/gtk.h>


static void add_panes (GtkWidget *paned, MooPanePosition pane_position)
{
    GtkWidget *textview;
    GtkTextBuffer *buffer;
    MooPaneLabel *label;

    textview = gtk_text_view_new ();
    gtk_text_view_set_wrap_mode (GTK_TEXT_VIEW (textview), GTK_WRAP_WORD);
    buffer = gtk_text_view_get_buffer (GTK_TEXT_VIEW (textview));
    gtk_text_buffer_insert_at_cursor (buffer, "Hi there. Hi there. "
            "Hi there. Hi there. Hi there. Hi there. Hi there. ", -1);
    label = moo_pane_label_new (GTK_STOCK_OK, NULL, "TextView", "TextView");
    moo_big_paned_insert_pane (MOO_BIG_PANED (paned), textview, label,
                               pane_position, -1);
    moo_pane_label_free (label);

    label = moo_pane_label_new (GTK_STOCK_CANCEL, NULL, "A label", "A label");
    moo_big_paned_insert_pane (MOO_BIG_PANED (paned),
                               gtk_label_new ("foolala"),
                               label, pane_position, -1);
    moo_pane_label_free (label);
}


int main (int argc, char *argv[])
{
    GtkWidget *window, *paned, *textview, *swin;
    GtkTextBuffer *buffer;

    gtk_init (&argc, &argv);
//     gdk_window_set_debug_updates (TRUE);

    window = gtk_window_new (GTK_WINDOW_TOPLEVEL);
    gtk_window_set_default_size (GTK_WINDOW (window), 800, 600);
    g_signal_connect (window, "destroy",
                      G_CALLBACK (gtk_main_quit), NULL);

    paned = moo_big_paned_new ();
    g_object_set (paned, "enable-detaching", TRUE, NULL);
    gtk_widget_show (paned);
    gtk_container_add (GTK_CONTAINER (window), paned);

    textview = gtk_text_view_new ();
    gtk_widget_show (textview);
    swin = gtk_scrolled_window_new (NULL, NULL);
    gtk_scrolled_window_set_policy (GTK_SCROLLED_WINDOW (swin),
                                    GTK_POLICY_AUTOMATIC,
                                    GTK_POLICY_AUTOMATIC);
    moo_big_paned_add_child (MOO_BIG_PANED (paned), swin);
//     gtk_container_add (GTK_CONTAINER (swin), textview);
    gtk_scrolled_window_add_with_viewport (GTK_SCROLLED_WINDOW (swin), gtk_label_new ("LABEL"));
    gtk_widget_show_all (swin);

    gtk_text_view_set_wrap_mode (GTK_TEXT_VIEW (textview), GTK_WRAP_WORD);
    buffer = gtk_text_view_get_buffer (GTK_TEXT_VIEW (textview));
    gtk_text_buffer_insert_at_cursor (buffer, "Click a button. Click a button. "
            "Click a button. Click a button. Click a button. Click a button. "
                    "Click a button. Click a button. Click a button. Click a button. "
                    "Click a button. Click a button. Click a button. Click a button. "
                    "Click a button. Click a button. Click a button. Click a button. "
                    "Click a button. Click a button. Click a button. Click a button. "
                    "Click a button. Click a button. Click a button. Click a button. "
                    "Click a button. Click a button. Click a button. Click a button. "
                    "Click a button. Click a button. Click a button. Click a button. "
                    "Click a button. Click a button. Click a button. Click a button. "
                    "Click a button. Click a button. Click a button. Click a button. "
                    "Click a button. Click a button. Click a button. Click a button. ",
            -1);

    add_panes (paned, MOO_PANE_POS_RIGHT);
    add_panes (paned, MOO_PANE_POS_LEFT);
    add_panes (paned, MOO_PANE_POS_TOP);
    add_panes (paned, MOO_PANE_POS_BOTTOM);

    gtk_widget_show_all (window);

    gtk_main ();

    return 0;
}
