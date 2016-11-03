#define _GNU_SOURCE
#include <stdio.h>
#include <stdlib.h>
#include <arpa/inet.h>
#include <string.h>
#include <stdint.h>
#include <stdbool.h>
#include <time.h>


#define FLOW_COLS		8
#define uint			unsigned int


uint32_t ip2int(const char* ip)
{
	uint32_t res = 0;
	inet_pton(AF_INET, ip, &res);
	return htonl(res);
}


uint str_split(char* str, const char* delimiter, char** pInChunks)
{
	char* dat = strtok(str, " ");
	register uint n=0;
	while(dat)
	{
		pInChunks[n++] = dat;
		dat = strtok(NULL, " ");
	}
	return n;
}


void curtime(char* pInStrTime, const uint maxlen)
{
	time_t rawtime;
	time( &rawtime );
	strftime(pInStrTime, maxlen, "flowstat_%d%m%Y", localtime( &rawtime ));
}


void convert(char* query, char* pInRes)
{
	char* chunks[FLOW_COLS] = {NULL};

	int chunk_count = str_split(query, " ", chunks);

	if(chunk_count < 7)
	{
		printf("Too short input line\n");
		exit(1);
	}

	uint32_t src_ip		= ip2int(chunks[0]);
	uint32_t dst_ip		= ip2int(chunks[1]);
	uint proto			= atoi(chunks[2]);
	uint16_t src_port	= ip2int(chunks[3]);
	uint16_t dst_port	= ip2int(chunks[4]);
	uint octets			= atoi(chunks[5]);
	uint packets		= atoi(chunks[6]);

	sprintf(pInRes, ",(%u,%u,%u,%u,%u,%u,%u)\0",
		src_ip, dst_ip, proto, src_port, dst_port, octets, packets);
}


int main()
{
	char buf_result_convert[0xff] = {0};
	FILE* f = stdin;
	char* input_line = malloc(0xff);
	size_t input_line_len = 0;
	ssize_t read_len = 0;
	char table_name[19] = {0};

	curtime(table_name, 19);

	printf("CREATE TABLE IF NOT EXISTS %s (\n", table_name);
	printf("`id` int(10) AUTO_INCREMENT NOT NULL,\n");
	printf("`src_ip` INT(10) UNSIGNED NOT NULL,\n");
	printf("`dst_ip` INT(10) UNSIGNED NOT NULL,\n");
	printf("`proto` smallint(2) unsigned NOT NULL DEFAULT 0,\n");
	printf("`src_port` smallint(5) unsigned NOT NULL DEFAULT 0,\n");
	printf("`dst_port` smallint(5) unsigned NOT NULL DEFAULT 0,\n");
	printf("`octets` INT unsigned NOT NULL DEFAULT 0,\n");
	printf("`packets` INT unsigned NOT NULL DEFAULT 0,\n");
	printf("PRIMARY KEY (`id`)\n");
	printf(") ENGINE=MyISAM DEFAULT CHARSET=utf8;\n");

	char ins_sql[0xff] = {0};
	sprintf(ins_sql, "INSERT INTO %s(`src_ip`, `dst_ip`, `proto`, `src_port`, `dst_port`, `octets`, `packets`) VALUES", table_name);

	// always none
	read_len = getline(&input_line, &input_line_len, f);

	while(true)
	{
		register uint n=0xfff;
		read_len = getline(&input_line, &input_line_len, f);
		if(read_len <= 0)
			break;
		convert(input_line, buf_result_convert);

		printf("%s\n", ins_sql);

		// without first comma
		printf("%s\n", buf_result_convert+1);

		while(n>0)
		{
			read_len = getline(&input_line, &input_line_len, f);
			if(read_len <= 0)
				break;
			convert(input_line, buf_result_convert);
			printf("%s\n", buf_result_convert);
			n--;
		}
		putc(';', stdout);
	}

	free(input_line);
	return 0;
}
