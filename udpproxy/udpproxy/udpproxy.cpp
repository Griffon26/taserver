
#include <assert.h>
#include <map>
#include <string.h>
#include <utility>
#include <stdio.h>
#include <vector>
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
        assert(bytesReceivedThisTime != SOCKET_ERROR);
        if (bytesReceivedThisTime == 0)
        {
            return bytesReceived;
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

        unsigned long messageSize;
        ret = recvall(controllerSocket, (char *)&messageSize, sizeof(unsigned long));
        assert(ret == sizeof(unsigned long));
        char pBuffer[32];
        ret = recvall(controllerSocket, pBuffer, messageSize);
        assert(ret == messageSize);

        closesocket(controllerSocket);

        if (!strncmp("reset", pBuffer, 5))
        {
            pControlData->allowedClients.removeAll();
        }
        else
        {
            assert(pBuffer[0] == 'r' || pBuffer[0] == 'a');
            unsigned long player_id = *(unsigned long *)&pBuffer[1];
            unsigned long address = *(unsigned long *)&pBuffer[1 + sizeof(unsigned long)];

            if (pBuffer[0] == 'a')
            {
                pControlData->allowedClients.addClient(player_id, address);
            }
            else
            {
                pControlData->allowedClients.removeClient(player_id, address);
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
            int lastError = WSAGetLastError();

            // When a client is removed from the server the proxy closes the 
            // game server socket to signal this thread that it should stop 
            // communication with the client; no need to log an error.
            if (lastError != WSAENOTSOCK)
            {
                printf("Recv from game server failed with error %d\n", lastError);
            }
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

    ULONGLONG timeOfLastSocketCleanup = GetTickCount64();
    while (true)
    {
        SOCKADDR_IN clientAddress;
        int clientAddressSize = sizeof(clientAddress);
        int bytesToSend = recvfrom(clientSocket, socketBuffer, sizeof(socketBuffer), 0, (sockaddr *)&clientAddress, &clientAddressSize);
        assert(bytesToSend != SOCKET_ERROR);

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
                    ret = closesocket(it->second.gameserverSocket);
                    assert(ret == 0);
                    it = clientDataMap.erase(it);
                }
                else
                {
                    it++;
                }
            }

            timeOfLastSocketCleanup = currentTickCount;
        }

        unsigned long clientIPInHostOrder = clientAddress.sin_addr.S_un.S_addr;
        unsigned short clientPort = clientAddress.sin_port;
        bool allowed = controlData.allowedClients.checkAllowedAndStorePort(clientIPInHostOrder, clientAddress.sin_port);
        auto key = std::make_pair(clientAddress.sin_addr.S_un.S_addr, clientAddress.sin_port);
        if (allowed || isPrivateAddress(clientIPInHostOrder))
        {
            auto it = clientDataMap.find(key);
            SOCKET gameserverSocket;
            ClientData *pClientData;
            if (it != clientDataMap.end())
            {
                pClientData = &it->second;
                gameserverSocket = pClientData->gameserverSocket;
            }
            else
            {
                pClientData = &clientDataMap[key];

                gameserverSocket = socket(AF_INET, SOCK_DGRAM, 0);
                ret = connect(gameserverSocket, (sockaddr *)&gameserverAddress, sizeof(gameserverAddress));
                assert(ret == 0);

                pClientData->gameserverSocket = gameserverSocket;
                pClientData->clientAddress = clientAddress;

                HANDLE threadHandle = CreateThread(NULL, 0, gameserverToClientHandler, &clientDataMap[key], 0, NULL);
                assert(threadHandle != NULL);
            }
            pClientData->timeOfLastMessage = currentTickCount;

            int bytesSent = 0;
            while (bytesSent < bytesToSend)
            {
                int bytesSentThisTime = send(gameserverSocket, &socketBuffer[bytesSent], bytesToSend - bytesSent, 0);
                assert(bytesSentThisTime != SOCKET_ERROR);
                //printf("Sent %d bytes to game server\n", bytesSentThisTime);
                bytesSent += bytesSentThisTime;
            }
        }
        else
        {
            auto it = clientDataMap.find(key);
            if (it != clientDataMap.end())
            {
                ret = closesocket(it->second.gameserverSocket);
                assert(ret == 0);
                it = clientDataMap.erase(it);
            }
        }
    }
    assert(false);
    return 0;
}

