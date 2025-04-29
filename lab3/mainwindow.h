#ifndef MAINWINDOW_H
#define MAINWINDOW_H

#include <QMainWindow>
#include <QLineEdit>
#include <QComboBox>
#include <QPushButton>
#include <QLabel>
#include <QVBoxLayout>
#include <QHBoxLayout>

class MainWindow : public QMainWindow
{
    Q_OBJECT

public:
    MainWindow(QWidget *parent = nullptr);
    ~MainWindow();

private slots:
    void convertNumber();
    void inputChanged(const QString &text);

private:
    QLineEdit *inputField;
    QLineEdit *outputField;
    QComboBox *fromBase;
    QComboBox *toBase;
    QPushButton *convertButton;
    QString convertBase(const QString &number, int fromBase, int toBase);
};

#endif 