#include "../../path.h"

void path_normalize(char *in, char *out) {
	char ch;
	int i = 0;
	while ((ch = in[i++]) != '\0')
		out[i] = in[i] == '/' ? '\\' : in[i];
	out[i] = '\0'; 
}