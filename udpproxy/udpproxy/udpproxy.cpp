
#include <assert.h>
#include <map>
#include <set>
#include <string.h>
#include <utility>
#include <stdio.h>
#include <Ws2tcpip.h>
#include <WinSock2.h>

#pragma comment(lib, "Ws2_32.lib")

#define CONTROL_MESSAGE_SIZE 5

/*
 * Performance measurement on a t2-micro showed that with 30 clients in the generator sending 32 bytes and sleeping 1 ms in between,
 * the CPU usage of the proxy was between 5% and 11% and the traffic was 1.8Mbps in both directions.
 */

char socketBuffer[1024 * 1024];
SOCKET clientSocket;
SOCKET gameServerSockets[1024];

class AllowedClients
{
private:
    CRITICAL_SECTION criticalSection;
    std::set<unsigned long> clientList;

public:
    AllowedClients()
    {
        InitializeCriticalSection(&criticalSection);
    }

    virtual ~AllowedClients()
    {
        DeleteCriticalSection(&criticalSection);
    }

    void addClient(unsigned long address)
    {
        EnterCriticalSection(&criticalSection);
        assert(!hasClient(address));
        clientList.insert(address);
        LeaveCriticalSection(&criticalSection);
    }
    void removeClient(unsigned long address)
    {
        EnterCriticalSection(&criticalSection);
        assert(hasClient(address));
        clientList.erase(address);
        LeaveCriticalSection(&criticalSection);
    }
    void removeAll()
    {
        EnterCriticalSection(&criticalSection);
        clientList.clear();
        LeaveCriticalSection(&criticalSection);
    }

    bool hasClient(unsigned long address)
    {
        EnterCriticalSection(&criticalSection);
        bool found = clientList.find(address) != clientList.end();
        LeaveCriticalSection(&criticalSection);

        return found;
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
        assert(bytesReceivedThisTime != SOCKET_ERROR);
        if (bytesReceivedThisTime == 0)
        {
            return 0;
        }
        bytesReceived += bytesReceivedThisTime;
    }

    assert(bytesReceived == len);
    return bytesReceived;
}

DWORD WINAPI allowedClientsHandler(void *pParam)
{
    int ret;
    ControlData *pControlData = (ControlData *)pParam;

    while (true)
    {
        SOCKADDR_IN sockaddr_in;
        int addressSize = sizeof(sockaddr_in);

        SOCKET controllerSocket = accept(pControlData->listenSocket, (sockaddr *)&sockaddr_in, &addressSize);
        assert(controllerSocket != INVALID_SOCKET);

        char pBuffer[CONTROL_MESSAGE_SIZE];
        ret = recvall(controllerSocket, pBuffer, CONTROL_MESSAGE_SIZE);
        assert(ret == CONTROL_MESSAGE_SIZE);

        closesocket(controllerSocket);

        if (!strncmp("reset", pBuffer, CONTROL_MESSAGE_SIZE))
        {
            pControlData->allowedClients.removeAll();
        }
        else
        {
            assert(pBuffer[0] == 'r' || pBuffer[0] == 'a');
            unsigned long address = *(unsigned long *)&pBuffer[1];

            if (pBuffer[0] == 'a')
            {
                pControlData->allowedClients.addClient(address);
            }
            else
            {
                pControlData->allowedClients.removeClient(address);
            }
        }
    }
}

DWORD WINAPI gameserverToClientHandler(void *pParam)
{
    ClientData *pClientData = (ClientData *)pParam;
    char buffer[64 * 1024];

    while (true)
    {
        int ret = recv(pClientData->gameserverSocket, buffer, sizeof(buffer), 0);
        if (ret == SOCKET_ERROR)
        {
            printf("Recv from game server failed with error %d\n", WSAGetLastError());
            break;
        }
        assert(ret != 0);

        int bytesToSend = ret;
        //printf("Received %d bytes from game server\n", bytesToSend);

        while (bytesToSend > 0)
        {
            int bytesSent = sendto(clientSocket, buffer, bytesToSend, 0, (sockaddr *)&pClientData->clientAddress, sizeof(pClientData->clientAddress));
            if (bytesSent == SOCKET_ERROR)
            {
                printf("Send to client failed with error %d\n", WSAGetLastError());
            }
            assert(bytesSent != SOCKET_ERROR);
            //printf("Sent %d bytes to client\n", bytesSent);
            bytesToSend -= bytesSent;
        }
    }

    printf("Exiting gameserver-to-client thread\n");
    return 0;
}

int main()
{
    int ret = 0;
    WSADATA wsaData;

    ControlData controlData;

    std::map<std::pair<unsigned long, int>, ClientData> clientDataMap;

    ret = WSAStartup((2, 2), &wsaData);
    assert(ret == 0);

    SOCKADDR_IN controlListenAddress;
    controlListenAddress.sin_family = AF_INET;
    ret = InetPtonA(AF_INET, "127.0.0.1", &(controlListenAddress.sin_addr));
    assert(ret == 1);
    controlListenAddress.sin_port = htons(9802);

    controlData.listenSocket = socket(AF_INET, SOCK_STREAM, 0);
    ret = bind(controlData.listenSocket, (sockaddr *)&controlListenAddress, sizeof(controlListenAddress));
    assert(ret != SOCKET_ERROR);

    ret = listen(controlData.listenSocket, SOMAXCONN);
    assert(ret != SOCKET_ERROR);

    HANDLE threadHandle = CreateThread(NULL, 0, allowedClientsHandler, &controlData, 0, NULL);
    assert(threadHandle != NULL);




    SOCKADDR_IN clientListenAddress;
    clientListenAddress.sin_family = AF_INET;
    clientListenAddress.sin_addr.s_addr = htonl(INADDR_ANY);
    clientListenAddress.sin_port = htons(7778);

    clientSocket = socket(AF_INET, SOCK_DGRAM, 0);
    ret = bind(clientSocket, (sockaddr *)&clientListenAddress, sizeof(clientListenAddress));
    assert(ret != SOCKET_ERROR);

    SOCKADDR_IN gameserverAddress;
    gameserverAddress.sin_family = AF_INET;
    ret = InetPtonA(AF_INET, "127.0.0.1", &(gameserverAddress.sin_addr));;
    assert(ret == 1);
    gameserverAddress.sin_port = htons(7777);


    while (true)
    {
        SOCKADDR_IN clientAddress;
        int clientAddressSize = sizeof(clientAddress);
        int bytesToSend = recvfrom(clientSocket, socketBuffer, sizeof(socketBuffer), 0, (sockaddr *)&clientAddress, &clientAddressSize);
        assert(bytesToSend != SOCKET_ERROR);

        //printf("Received %d bytes from client\n", bytesToSend);


        unsigned long clientIPInHostOrder = clientAddress.sin_addr.S_un.S_addr;
        if (isPrivateAddress(clientIPInHostOrder) ||
            controlData.allowedClients.hasClient(clientIPInHostOrder))
        {
            auto key = std::make_pair(clientAddress.sin_addr.S_un.S_addr, clientAddress.sin_port);
            auto it = clientDataMap.find(key);
            SOCKET gameserverSocket;
            if (it != clientDataMap.end())
            {
                gameserverSocket = it->second.gameserverSocket;
            }
            else
            {
                gameserverSocket = socket(AF_INET, SOCK_DGRAM, 0);
                ret = connect(gameserverSocket, (sockaddr *)&gameserverAddress, sizeof(gameserverAddress));
                assert(ret == 0);

                clientDataMap[key].gameserverSocket = gameserverSocket;
                clientDataMap[key].clientAddress = clientAddress;

                HANDLE threadHandle = CreateThread(NULL, 0, gameserverToClientHandler, &clientDataMap[key], 0, NULL);
                assert(threadHandle != NULL);
            }

            int bytesSent = 0;
            while (bytesSent < bytesToSend)
            {
                int bytesSentThisTime = send(gameserverSocket, &socketBuffer[bytesSent], bytesToSend - bytesSent, 0);
                assert(bytesSentThisTime != SOCKET_ERROR);
                //printf("Sent %d bytes to game server\n", bytesSentThisTime);
                bytesSent += bytesSentThisTime;
            }
        }
    }
    assert(false);
    return 0;
}

