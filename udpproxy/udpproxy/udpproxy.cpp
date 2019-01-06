
#include <map>
#include <stdio.h>
#include <string.h>
#include <utility>
#include <vector>
#include <WinSock2.h>
#include <Ws2tcpip.h>

#pragma comment(lib, "Ws2_32.lib")

#define SIO_UDP_CONNRESET _WSAIOW(IOC_VENDOR, 12)

#define MIN_PORT 2000
#define MAX_PORT 9000

char socketBuffer[64 * 1024];
SOCKET clientSocket;

class AllowedClients
{
private:
    struct ClientInfo
    {
        unsigned long playerId;
        unsigned long address;
        unsigned long port;
    };

    CRITICAL_SECTION criticalSection;

    std::vector<ClientInfo> clientList;

public:
    AllowedClients()
    {
        InitializeCriticalSection(&criticalSection);
    }

    virtual ~AllowedClients()
    {
        DeleteCriticalSection(&criticalSection);
    }

    void addClient(unsigned long playerId, unsigned long address)
    {
        EnterCriticalSection(&criticalSection);
        // When allowing a new player the clientList entry has no port yet;
        // that will be filled in once we receive the first packet.
        clientList.push_back({ playerId, address, 0 });
        LeaveCriticalSection(&criticalSection);
    }
    void removeClient(unsigned long playerId, unsigned long address)
    {
        (void)address;

        EnterCriticalSection(&criticalSection);
        for (auto iter = clientList.begin(); iter != clientList.end(); iter++)
        {
            if (iter->playerId == playerId)
            {
                clientList.erase(iter);
                break;
            }
        }
        LeaveCriticalSection(&criticalSection);
    }
    void removeAll()
    {
        EnterCriticalSection(&criticalSection);
        clientList.clear();
        LeaveCriticalSection(&criticalSection);
    }

    bool checkAllowedAndStorePort(unsigned long address, unsigned long port)
    {
        bool allowed = false;
        EnterCriticalSection(&criticalSection);
        
        ClientInfo *pNewClient = NULL;
        for (auto iter = clientList.begin(); iter != clientList.end(); iter++)
        {
            if (iter->address == address)
            {
                if (iter->port == port)
                {
                    allowed = true;
                    break;
                }
                else if (iter->port == 0)
                {
                    pNewClient = &*iter;
                }
            }
        }

        // If there's no entry with our port in the clientList but there is
        // a matching entry without a port, then claim that for ourselves.
        if (!allowed && pNewClient)
        {
            fprintf(stderr, "forwarder: associating new connection on port %d with client at %d.%d.%d.%d\n",
                port,
                (pNewClient->address >> 0) & 0xFF,
                (pNewClient->address >> 8) & 0xFF,
                (pNewClient->address >> 16) & 0xFF,
                (pNewClient->address >> 24) & 0xFF);
                        
            pNewClient->port = port;
            allowed = true;
        }
        LeaveCriticalSection(&criticalSection);

        return allowed;
    }
};

struct ControlData
{
    SOCKET listenSocket;
    AllowedClients allowedClients;
};

struct ClientData
{
    SOCKADDR_IN clientAddress;
    SOCKET gameserverSocket;
    ULONGLONG timeOfLastMessage;
};

bool isPrivateAddress(unsigned long addressInNetworkOrder)
{
    unsigned long addressInHostOrder = ntohl(addressInNetworkOrder);
    return (
        (addressInHostOrder & 0xFF000000) == (127 << 24) ||
        (addressInHostOrder & 0xFF000000) == (10 << 24) ||
        (addressInHostOrder & 0xFFF00000) == ((172 << 24) | (16 << 16)) ||
        (addressInHostOrder & 0xFFFF0000) == ((192 << 24) | (168 << 16))
        );
}

int recvall(SOCKET socket, char *pBuffer, int len)
{
    int bytesReceived = 0;

    while (bytesReceived < len)
    {
        int bytesReceivedThisTime = recv(socket, &pBuffer[bytesReceived], len - bytesReceived, 0);
        switch (bytesReceivedThisTime)
        {
        case SOCKET_ERROR:
            return SOCKET_ERROR;
        case 0:
            return bytesReceived;
        default:
            bytesReceived += bytesReceivedThisTime;
            break;
        }
    }

    return bytesReceived;
}

class SocketCloser
{
public:
    SocketCloser(SOCKET socket):
        mSocket(socket)
    {
        //fprintf(stderr, "Initializing closer for socket %u\n", mSocket);
    }

    ~SocketCloser()
    {
        //fprintf(stderr, "Closing socket %u\n", mSocket);
        closesocket(mSocket);
    }

private:
    SOCKET mSocket;
};

DWORD WINAPI allowedClientsHandler(void *pParam)
{
    int ret;
    ControlData *pControlData = (ControlData *)pParam;

    while (true)
    {
        SOCKADDR_IN sockaddr_in;
        int addressSize = sizeof(sockaddr_in);

        SOCKET controllerSocket = accept(pControlData->listenSocket, (sockaddr *)&sockaddr_in, &addressSize);
        if (controllerSocket == INVALID_SOCKET) continue;
        SocketCloser socketCloser(controllerSocket);

        unsigned long messageSize;
        ret = recvall(controllerSocket, (char *)&messageSize, sizeof(unsigned long));
        if (ret != sizeof(unsigned long)) continue;

        char pBuffer[32];
        ret = recvall(controllerSocket, pBuffer, messageSize);
        if (ret != (int)messageSize) continue;

        if (!strncmp("reset", pBuffer, 5))
        {
            fprintf(stderr, "control: Received reset command\n");
            pControlData->allowedClients.removeAll();
        }
        else if((messageSize == 2 * sizeof(unsigned long) + 1) && 
                (pBuffer[0] == 'r' || pBuffer[0] == 'a'))
        {
            unsigned long playerId = *(unsigned long *)&pBuffer[1];
            unsigned long address = *(unsigned long *)&pBuffer[1 + sizeof(unsigned long)];

            if (pBuffer[0] == 'a')
            {
                fprintf(stderr, "control: adding client %d with IP %d.%d.%d.%d\n",
                    playerId,
                    (address >> 0) & 0xFF,
                    (address >> 8) & 0xFF,
                    (address >> 16) & 0xFF,
                    (address >> 24) & 0xFF);
                pControlData->allowedClients.addClient(playerId, address);
            }
            else
            {
                fprintf(stderr, "control: removing client %d with IP %d.%d.%d.%d\n",
                    playerId,
                    (address >> 0) & 0xFF,
                    (address >> 8) & 0xFF,
                    (address >> 16) & 0xFF,
                    (address >> 24) & 0xFF);
                pControlData->allowedClients.removeClient(playerId, address);
            }
        }
        else
        {
            // ignore invalid command
        }
    }
}

DWORD WINAPI gameserverToClientHandler(void *pParam)
{
    SOCKADDR_IN clientAddress = ((ClientData *)pParam)->clientAddress;
    SOCKET gameserverSocket = ((ClientData *)pParam)->gameserverSocket;

    // Don't access the data through the pointer passed to this function after this point,
    // because it may have been removed before this thread has terminated.
    pParam = NULL;

    char buffer[64 * 1024];

    while (true)
    {
        int ret = recv(gameserverSocket, buffer, sizeof(buffer), 0);
        if (ret == SOCKET_ERROR)
        {
            int lastError = WSAGetLastError();

            // When a client is removed from the server the proxy closes the 
            // game server socket to signal this thread that it should stop 
            // communication with the client; no need to log an error.
            if (lastError != WSAEINTR)
            {
                fprintf(stderr, "Receive from game server failed, error %d\n", lastError);
            }
            break;
        }
        else if (ret == 0)
        {
            break;
        }

        int bytesToSend = ret;
        //printf("Received %d bytes from game server\n", bytesToSend);

        while (bytesToSend > 0)
        {
            int bytesSent = sendto(clientSocket, buffer, bytesToSend, 0, (sockaddr *)&clientAddress, sizeof(clientAddress));
            if (bytesSent == SOCKET_ERROR)
            {
                // Only report this error, but otherwise ignore it because losing
                // packets is ok for UDP
                fprintf(stderr, "Send to client failed, error %d\n", WSAGetLastError());
            }
            //printf("Sent %d bytes to client\n", bytesSent);
            bytesToSend -= bytesSent;
        }
    }

    printf("Exiting gameserver-to-client thread for client %d.%d.%d.%d:%d\n",
        clientAddress.sin_addr.S_un.S_un_b.s_b1,
        clientAddress.sin_addr.S_un.S_un_b.s_b2,
        clientAddress.sin_addr.S_un.S_un_b.s_b3,
        clientAddress.sin_addr.S_un.S_un_b.s_b4,
        clientAddress.sin_port);
    return 0;
}

void printUsage(char *pProgram)
{
	fprintf(stderr, "Usage: %s <port>\n\n", pProgram);
	fprintf(stderr, "Start a udpproxy that will forward from the specified port to the specified port + 100 on localhost;\n");
	fprintf(stderr, "The proxy will be listening for control connections on port + 200.\n");
	fprintf(stderr, "Valid values for port range from %d to %d.\n", MIN_PORT, MAX_PORT);
}

int main(int argc, char *argv[])
{
    int ret = 0;
    WSADATA wsaData;

    ControlData controlData;

    std::map<std::pair<unsigned long, int>, ClientData> clientDataMap;

	if (argc != 2)
	{
		fprintf(stderr, "Invalid number of parameters specified.\n\n");
		printUsage(argv[0]);
		return -1;
	}

	int port;
	if (sscanf_s(argv[1], "%d", &port) != 1)
	{
		fprintf(stderr, "Invalid value specified for port (must be a decimal value).\n\n");
		printUsage(argv[0]);
		return -1;
	}

	if ((port < MIN_PORT) || (port > MAX_PORT))
	{
		fprintf(stderr, "Invalid value specified for port (must be in the range %d-%d).\n\n", MIN_PORT, MAX_PORT);
		printUsage(argv[0]);
		return -1;
	}
	u_short clientPort = static_cast<u_short>(port);
	u_short gameServerPort = clientPort + 100;
	u_short controlPort = clientPort + 200;

    ret = WSAStartup((2, 2), &wsaData);
    if (ret != 0)
    {
        fprintf(stderr, "Failed to initialize winsock, error %d\n", ret);
        return -1;
    }

    SOCKADDR_IN controlListenAddress;
    controlListenAddress.sin_family = AF_INET;
    ret = InetPtonA(AF_INET, "127.0.0.1", &(controlListenAddress.sin_addr));
    if(ret != 1)
    {
        fprintf(stderr, "InetPtonA failed with error code %d, extended error %d\n", ret, WSAGetLastError());
        return -1;
    }
    controlListenAddress.sin_port = htons(controlPort);

    controlData.listenSocket = socket(AF_INET, SOCK_STREAM, 0);
    if (controlData.listenSocket == INVALID_SOCKET)
    {
        fprintf(stderr, "Failed to create socket for control connections, error %d\n", WSAGetLastError());
        return -1;
    }
    SocketCloser controlSocketCloser(controlData.listenSocket);

    ret = bind(controlData.listenSocket, (sockaddr *)&controlListenAddress, sizeof(controlListenAddress));
    if (ret == SOCKET_ERROR)
    {
        fprintf(stderr, "Failed to bind to listen address localhost:%d for control connections, error %d\n", controlPort, WSAGetLastError());
        return -1;
    }

    ret = listen(controlData.listenSocket, SOMAXCONN);
    if (ret == SOCKET_ERROR)
    {
        fprintf(stderr, "Failed to listen on control port, error %d\n", WSAGetLastError());
        return -1;
    }

    HANDLE controlThreadHandle = CreateThread(NULL, 0, allowedClientsHandler, &controlData, 0, NULL);
    if (controlThreadHandle == NULL)
    {
        fprintf(stderr, "Failed to start thread for the control channel, error %d\n", GetLastError());
        return -1;
    }




    SOCKADDR_IN clientListenAddress;
    clientListenAddress.sin_family = AF_INET;
    clientListenAddress.sin_addr.s_addr = htonl(INADDR_ANY);
    clientListenAddress.sin_port = htons(clientPort);

    clientSocket = socket(AF_INET, SOCK_DGRAM, 0);
    if (clientSocket == INVALID_SOCKET)
    {
        fprintf(stderr, "Failed to create socket for client connections, error %d\n", WSAGetLastError());
        return -1;
    }
    SocketCloser clientSocketCloser(clientSocket);

    u_long falseValue = false;
    if (ioctlsocket(clientSocket, SIO_UDP_CONNRESET, &falseValue) == SOCKET_ERROR)
    {
        fprintf(stderr, "Failed to set SIO_UDP_CONNRESET to False on client socket, error %d\n", WSAGetLastError());
        return -1;
    }

    ret = bind(clientSocket, (sockaddr *)&clientListenAddress, sizeof(clientListenAddress));
    if (ret == SOCKET_ERROR)
    {
        fprintf(stderr, "Failed to bind to listen address 0.0.0.0:%d for client connections, error %d\n", clientPort, WSAGetLastError());
        return -1;
    }

    SOCKADDR_IN gameserverAddress;
    gameserverAddress.sin_family = AF_INET;
    ret = InetPtonA(AF_INET, "127.0.0.1", &(gameserverAddress.sin_addr));;
    if (ret != 1)
    {
        fprintf(stderr, "InetPtonA failed with error code %d, extended error %d\n", ret, WSAGetLastError());
        return -1;
    }
    gameserverAddress.sin_port = htons(gameServerPort);

    ULONGLONG timeOfLastSocketCleanup = GetTickCount64();
    while (true)
    {
        SOCKADDR_IN clientAddress;
        int clientAddressSize = sizeof(clientAddress);
        int bytesToSend = recvfrom(clientSocket, socketBuffer, sizeof(socketBuffer), 0, (sockaddr *)&clientAddress, &clientAddressSize);
        if (bytesToSend == SOCKET_ERROR)
        {
            fprintf(stderr, "Failed to receive from the client socket, error %d. Exiting...\n", WSAGetLastError());
            break;
        }

        //printf("Received %d bytes from client\n", bytesToSend);

        /*
         * Automatic cleanup after inactivity will clean up sockets for
         * clients who willingly stop sending packets to the game server
         * and clients with private IP addresses. Other clients' sockets
         * will be removed when they send the first packet after being
         * blocked.
         */
        ULONGLONG currentTickCount = GetTickCount64();
        ULONGLONG oneMinute = 1 * 60 * 1000;
        if (currentTickCount > timeOfLastSocketCleanup + oneMinute)
        {
            for (auto it = clientDataMap.begin(); it != clientDataMap.end();)
            {
                if (it->second.timeOfLastMessage <= timeOfLastSocketCleanup)
                {
                    fprintf(stderr, "forwarder: cleaning up... closing socket for client %d.%d.%d.%d:%d\n",
                            it->second.clientAddress.sin_addr.S_un.S_un_b.s_b1,
                            it->second.clientAddress.sin_addr.S_un.S_un_b.s_b2,
                            it->second.clientAddress.sin_addr.S_un.S_un_b.s_b3,
                            it->second.clientAddress.sin_addr.S_un.S_un_b.s_b4,
                            it->second.clientAddress.sin_port);
                    //fprintf(stderr, "Closing gameserver socket %u\n", it->second.gameserverSocket);
                    ret = closesocket(it->second.gameserverSocket);
                    if (ret != 0)
                    {
                        fprintf(stderr, "Failed to close the game server socket for a client during inactivity cleanup, error %d. Ignoring...\n", WSAGetLastError());
                    }
                    it = clientDataMap.erase(it);
                }
                else
                {
                    it++;
                }
            }

            timeOfLastSocketCleanup = currentTickCount;
        }

        unsigned long clientIPInNetworkOrder = clientAddress.sin_addr.S_un.S_addr;
        bool allowed = controlData.allowedClients.checkAllowedAndStorePort(clientIPInNetworkOrder, clientAddress.sin_port);
        auto key = std::make_pair(clientAddress.sin_addr.S_un.S_addr, clientAddress.sin_port);
        if (allowed || isPrivateAddress(clientIPInNetworkOrder))
        {
            auto it = clientDataMap.find(key);
            ClientData *pClientData;
            if (it != clientDataMap.end())
            {
                pClientData = &it->second;
            }
            else
            {
                ClientData clientData;

                SOCKET gameserverSocket = socket(AF_INET, SOCK_DGRAM, 0);
                if (gameserverSocket == INVALID_SOCKET)
                {
                    fprintf(stderr, "Failed to create a game server socket for allowed client %d.%d.%d.%d:%d, error %d\n",
                        clientAddress.sin_addr.S_un.S_un_b.s_b1,
                        clientAddress.sin_addr.S_un.S_un_b.s_b2,
                        clientAddress.sin_addr.S_un.S_un_b.s_b3,
                        clientAddress.sin_addr.S_un.S_un_b.s_b4,
                        clientAddress.sin_port,
                        WSAGetLastError());
                    break;
                }

                ret = connect(gameserverSocket, (sockaddr *)&gameserverAddress, sizeof(gameserverAddress));
                if (ret != 0)
                {
                    fprintf(stderr, "Failed to connect to game server address, error %d\n", WSAGetLastError());
                    break;
                }

                clientData.gameserverSocket = gameserverSocket;
                clientData.clientAddress = clientAddress;

                clientDataMap[key] = clientData;
                pClientData = &clientDataMap[key];

                HANDLE clientThreadHandle = CreateThread(NULL, 0, gameserverToClientHandler, pClientData, 0, NULL);
                if (clientThreadHandle == NULL)
                {
                    fprintf(stderr, "Failed to start thread for game server to client communication, error %d\n", GetLastError());
                    break;
                }
            }
            pClientData->timeOfLastMessage = currentTickCount;

            int bytesSent = 0;
            while (bytesSent < bytesToSend)
            {
                int bytesSentThisTime = send(pClientData->gameserverSocket, &socketBuffer[bytesSent], bytesToSend - bytesSent, 0);
                if (bytesSentThisTime == SOCKET_ERROR)
                {
                    fprintf(stderr, "Failed to send client data to game server, error %d. Ignoring...\n", WSAGetLastError());
                    break;
                }
                //printf("Sent %d bytes to game server\n", bytesSentThisTime);
                bytesSent += bytesSentThisTime;
            }
        }
        else
        {
            auto it = clientDataMap.find(key);
            if (it != clientDataMap.end())
            {
                fprintf(stderr, "forwarder: client not allowed, closing socket for client %d.%d.%d.%d:%d\n",
                    it->second.clientAddress.sin_addr.S_un.S_un_b.s_b1,
                    it->second.clientAddress.sin_addr.S_un.S_un_b.s_b2,
                    it->second.clientAddress.sin_addr.S_un.S_un_b.s_b3,
                    it->second.clientAddress.sin_addr.S_un.S_un_b.s_b4,
                    it->second.clientAddress.sin_port);
                //fprintf(stderr, "Closing gameserver socket %u\n", it->second.gameserverSocket);
                ret = closesocket(it->second.gameserverSocket);
                if (ret != 0)
                {
                    // Ignoring this error would leave the gameserver-to-client thread running.
                    // I definitely want to know (through bug reports) if this ever fails so I can
                    // find a better way to handle this situation.
                    fprintf(stderr, "Failed to close game server socket for removed client, error %d.\n", WSAGetLastError());
                    break;
                }
                it = clientDataMap.erase(it);
            }
        }
    }

    ret = WSACleanup();
    if (ret == SOCKET_ERROR)
    {
        fprintf(stderr, "Failed to cleanup winsock, error %d\n", WSAGetLastError());
    }
    
    fprintf(stderr, "*********** UDP proxy is exiting! ***********\n");
    return 0;
}

