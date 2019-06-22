# Define the symbols we might want to change:
CC	?= gcc
CFLAGS += -g

OBJECTS	:= main.o lib/lib.o

main: $(OBJECTS)
	$(CC) $(CFLAGS) $(OBJECTS) -o main

main.o: main.c
	$(CC) $(INCLUDES) $(CFLAGS) -c main.c -o main.o

lib/lib.o: lib/lib.c
	$(CC) $(CFLAGS) -c lib/lib.c -o lib/lib.o

clean: 
	rm -f main main.o lib/lib.o