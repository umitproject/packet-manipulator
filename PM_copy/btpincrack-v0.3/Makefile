CC = gcc
CFLAGS = -Wall -O2 -funroll-loops
TARGET = btpincrack
LDFLAGS =
OBJS = safer.o\
       e.o\
       main.o\
       ../picod/libpicod.c

all: btpincrack

btpincrack: $(OBJS)
	$(CC) $(CFLAGS) -o $(TARGET) $(OBJS) $(LDFLAGS)

clean:
	rm -f *.o *.core $(TARGET)
