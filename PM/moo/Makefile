HEADERS = moopaned.h moopane.h moobigpaned.h moomarshals.h stock-moo.h
OBJECTS = moopaned.o moopane.o moobigpaned.o test.o moomarshals.o
PICS = close.png sticky.png hide.png detach.png attach.png keepontop.png

CFLAGS = `pkg-config --cflags gtk+-2.0` -W -Wall -DMooPane=_PidaMooPane \
-DMooPaneClass=_PidaMooPaneClass -DMooPaned=_PidaMooPaned -DMooPanedClass=_PidaMooPanedClass \
-DMooBigPaned=_PidaMooBigPaned -DMooBigPanedClass=_PidaMooBigPanedClass
LIBS = `pkg-config --libs gtk+-2.0`
PYGTK_DEFS_DIR=`pkg-config --variable=defsdir pygtk-2.0`

test: $(OBJECTS)
	gcc $(LIBS) $(OBJECTS) -o test

moomarshals.c: moomarshals.list
	echo '#include "moomarshals.h"' > $@.tmp &&	\
	glib-genmarshal --prefix=_moo_marshal --body	\
	       moomarshals.list >> $@.tmp && mv $@.tmp $@
moomarshals.h: moomarshals.list
	glib-genmarshal --prefix=_moo_marshal --header	\
	       moomarshals.list > $@.tmp && mv $@.tmp $@

stock-moo.h: $(PICS)
	gdk-pixbuf-csource --static --build-list	\
		MOO_HIDE_ICON hide.png			\
		MOO_CLOSE_ICON close.png		\
		MOO_STICKY_ICON sticky.png		\
		MOO_DETACH_ICON detach.png		\
		MOO_ATTACH_ICON attach.png		\
		MOO_KEEP_ON_TOP_ICON keepontop.png	\
			> $@.tmp && mv $@.tmp $@

%-prepro.c: %.c $(HEADERS)
	gcc $(CFLAGS) $*.c -c -E > $*-prepro.c
%.o: %.c $(HEADERS)
	gcc $(CFLAGS) $*.c -c -o $@
moomarshals.o: moomarshals.c moomarshals.h
	gcc $(CFLAGS) -Wno-unused moomarshals.c -c -o $@

clean:
	rm -f *.o test paned.tar.bz2 moomarshals.[ch] stock-moo.h moo-pygtk.c *.pyc

dist:
	rm -fr paned.tar.bz2 paned/ && \
	mkdir paned && \
	cp moo-stub.c moo.override moo.defs moopaned.override moopaned.defs \
		moopane.h moopaned.h moobigpaned.h $(PICS) \
		moopane.c moopaned.c moobigpaned.c test.c \
		moomarshals.list Makefile paned/ && \
	tar cjf paned.tar.bz2 paned/ && \
	rm -fr paned/

distcheck:
	make dist && tar xjf paned.tar.bz2 && cd paned && \
	make && make dist && mv paned.tar.bz2 ../ && \
	cd .. && rm -fr paned

prepare: moomarshals.c moomarshals.h stock-moo.h moo-pygtk.c

moo-pygtk.c: moo.defs moopaned.defs moo.override moopaned.override
	pygtk-codegen-2.0 --prefix _moo_stub \
		--register $(PYGTK_DEFS_DIR)/gtk-types.defs \
		--register $(PYGTK_DEFS_DIR)/gdk-types.defs \
		--override moo.override \
		--outfilename moo-pygtk.c \
		moo.defs > $@.tmp && \
		mv $@.tmp $@
