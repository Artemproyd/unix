#include <QApplication>
#include "mainwindow.h"

int main(int argc, char *argv[])
{
    // Завершать программу при ошибках
    qputenv("QT_FATAL_WARNINGS", "1");
    
    QApplication a(argc, argv);
    MainWindow w;
    w.show();
    return a.exec();
} 