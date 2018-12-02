#include <assert.h>
#include <stdio.h>
#include <WinSock2.h>
#include <Ws2tcpip.h>

#pragma comment(lib, "Ws2_32.lib")

#define SEND_SIZE 32
#define NR_OF_CLIENTS 30
#define REPORT_CHUNK 1024
#define SLEEP_TIME 1


struct ClientData
{
    int clientId;
    SOCKET socket;
};

ClientData clientData[NR_OF_CLIENTS];

DWORD WINAPI senderFunc(void *pParam)
{
    ClientData *pClientData = (ClientData *)pParam;
    char sendBuffer[SEND_SIZE];

    unsigned long long totalBytesSent = 0;
    unsigned long long lastPrintedTotalBytesSent = 0;

    while (true)
    {
        int bytesSent = 0;
        while (bytesSent < SEND_SIZE)
        {
            int bytesSentThisTime = send(pClientData->socket, &sendBuffer[bytesSent], SEND_SIZE - bytesSent, 0);
            assert(bytesSentThisTime != SOCKET_ERROR);
            bytesSent += bytesSentThisTime;
        }

        totalBytesSent += bytesSent;

        if (totalBytesSent >= lastPrintedTotalBytesSent + REPORT_CHUNK)
        {
            printf("Client %d: Total chunks of %d sent is %llu\n", pClientData->clientId, REPORT_CHUNK, totalBytesSent / REPORT_CHUNK);
            lastPrintedTotalBytesSent = totalBytesSent;
        }

        Sleep(SLEEP_TIME);
    }
}

DWORD WINAPI receiverFunc(void *pParam)
{
    ClientData *pClientData = (ClientData *)pParam;
    char receiveBuffer[10240];

    assert(sizeof(receiveBuffer) > SEND_SIZE);

    unsigned long long totalBytesReceived = 0;
    unsigned long long lastPrintedTotalBytesReceived = 0;

    while (true)
    {
        int bytesReceived = recv(pClientData->socket, receiveBuffer, sizeof(receiveBuffer), 0);
        assert(bytesReceived != SOCKET_ERROR);
        assert(bytesReceived <= sizeof(receiveBuffer));

        totalBytesReceived += bytesReceived;

        if (totalBytesReceived >= lastPrintedTotalBytesReceived + REPORT_CHUNK)
        {
            printf("Client %d: Total chunks of %d received is %llu\n", pClientData->clientId, REPORT_CHUNK, totalBytesReceived / REPORT_CHUNK);
            lastPrintedTotalBytesReceived = totalBytesReceived;
        }

    }
}

int main()
{
    int ret = 0;
    WSADATA wsaData;

    ret = WSAStartup((2, 2), &wsaData);
    assert(ret == 0);

    SOCKADDR_IN serverAddress;
    serverAddress.sin_family = AF_INET;
    ret = InetPtonA(AF_INET, "127.0.0.1", &(serverAddress.sin_addr));
    assert(ret == 1);
    serverAddress.sin_port = htons(7778);

    for (int i = 0; i < NR_OF_CLIENTS; i++)
    {
        clientData[i].clientId = i;
        clientData[i].socket = socket(AF_INET, SOCK_DGRAM, 0);
        ret = connect(clientData[i].socket, (sockaddr *)&serverAddress, sizeof(serverAddress));
        assert(ret == 0);

        HANDLE threadHandle = CreateThread(NULL, 0, senderFunc, &clientData[i], 0, NULL);
        assert(threadHandle != NULL);

        threadHandle = CreateThread(NULL, 0, receiverFunc, &clientData[i], 0, NULL);
        assert(threadHandle != NULL);
    }
    while (true);
}
