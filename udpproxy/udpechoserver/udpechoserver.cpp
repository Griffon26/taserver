#include <assert.h>
#include <stdio.h>
#include <WinSock2.h>
#include <Ws2tcpip.h>

#pragma comment(lib, "Ws2_32.lib")

char receiveBuffer[1024 * 1024];

int main()
{
    int ret = 0;
    WSADATA wsaData;

    ret = WSAStartup((2, 2), &wsaData);
    assert(ret == 0);

    SOCKADDR_IN listenAddress;
    listenAddress.sin_family = AF_INET;
    listenAddress.sin_addr.s_addr = htonl(INADDR_ANY);
    listenAddress.sin_port = htons(7777);

    SOCKET clientSocket = socket(AF_INET, SOCK_DGRAM, 0);
    ret = bind(clientSocket, (sockaddr *)&listenAddress, sizeof(listenAddress));
    assert(ret != SOCKET_ERROR);

    SOCKADDR_IN clientAddress;

    while (true)
    {
        int clientAddressSize = sizeof(clientAddress);
        int bytesReceived = recvfrom(clientSocket, receiveBuffer, sizeof(receiveBuffer), 0, (sockaddr *)&clientAddress, &clientAddressSize);
        int bytesSent = 0;
        printf("Received %d bytes\n", bytesReceived);
        while (bytesSent < bytesReceived)
        {
            int bytesSentThisTime = sendto(clientSocket, &receiveBuffer[bytesSent], bytesReceived - bytesSent, 0, (sockaddr *)&clientAddress, clientAddressSize);
            assert(bytesSentThisTime != SOCKET_ERROR);
            bytesSent += bytesSentThisTime;
            printf("Echoed %d bytes\n", bytesSentThisTime);
        }
    }
}
