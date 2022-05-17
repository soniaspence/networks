Assignment for networks course with same basis as other assignments with an added UDP layer

server
----------------------------------------------------------------------------------
To run the server execute the following statement:
	
python3 UDP_server.py

Can also be executed by substituting whatever version of python is installed
on your machine. Once it is executed a port number will be reported by the server.

client
---------------------------------------------------------------------------------
To run the client execute the following statement:

python3 UDP_client.py username chat://host:port

Same as server can use different versions of python. Make sure to sub username for
whatever username you want. Also sub host based on what your server is running 
(for example: localhost) and sub port for the number reported by the server
