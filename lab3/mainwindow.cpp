#include "mainwindow.h"
#include <QMessageBox>

MainWindow::MainWindow(QWidget *parent)
    : QMainWindow(parent)
{
    // Создаем центральный виджет и главный layout
    QWidget *centralWidget = new QWidget(this);
    QVBoxLayout *mainLayout = new QVBoxLayout(centralWidget);
    
    // Создаем и настраиваем поля ввода/вывода
    inputField = new QLineEdit(this);
    outputField = new QLineEdit(this);
    outputField->setReadOnly(true);
    
    // Создаем выпадающие списки для выбора систем счисления
    fromBase = new QComboBox(this);
    toBase = new QComboBox(this);
    
    // Добавляем варианты систем счисления
    QStringList bases = {"2 (BIN)", "8 (OCT)", "10 (DEC)", "16 (HEX)"};
    fromBase->addItems(bases);
    toBase->addItems(bases);
    
    // Устанавливаем десятичную систему по умолчанию
    fromBase->setCurrentIndex(2);
    
    // Создаем кнопку конвертации
    convertButton = new QPushButton("Конвертировать", this);
    convertButton->setEnabled(false);
    
    // Создаем горизонтальные layouts для организации элементов
    QHBoxLayout *inputLayout = new QHBoxLayout();
    QHBoxLayout *outputLayout = new QHBoxLayout();
    
    // Добавляем labels и поля в layouts
    inputLayout->addWidget(new QLabel("Из:"));
    inputLayout->addWidget(fromBase);
    inputLayout->addWidget(inputField);
    
    outputLayout->addWidget(new QLabel("В:"));
    outputLayout->addWidget(toBase);
    outputLayout->addWidget(outputField);
    
    // Добавляем все в главный layout
    mainLayout->addLayout(inputLayout);
    mainLayout->addLayout(outputLayout);
    mainLayout->addWidget(convertButton);
    
    // Устанавливаем центральный виджет
    setCentralWidget(centralWidget);
    
    // Устанавливаем заголовок окна и размеры
    setWindowTitle("Конвертер систем счисления");
    setMinimumSize(400, 150);
    
    // Подключаем сигналы к слотам
    connect(convertButton, &QPushButton::clicked, this, &MainWindow::convertNumber);
    connect(inputField, &QLineEdit::textChanged, this, &MainWindow::inputChanged);
}

MainWindow::~MainWindow()
{
}

void MainWindow::inputChanged(const QString &text)
{
    // Активируем кнопку только если поле ввода не пустое
    convertButton->setEnabled(!text.isEmpty());
}

void MainWindow::convertNumber()
{
    QString input = inputField->text().trimmed();
    if(input.isEmpty()) {
        return;
    }
    
    // Получаем основания систем счисления
    int from = fromBase->currentText().split(" ").first().toInt();
    int to = toBase->currentText().split(" ").first().toInt();
    
    try {
        QString result = convertBase(input, from, to);
        outputField->setText(result);
    }
    catch(const std::exception&) {
        QMessageBox::warning(this, "Ошибка", "Неверный формат числа для выбранной системы счисления");
    }
}

QString MainWindow::convertBase(const QString &number, int fromBase, int toBase)
{
    bool ok;
    // Преобразуем входное число в десятичное
    qlonglong decimal = number.toLongLong(&ok, fromBase);
    if(!ok) {
        throw std::invalid_argument("Invalid number format");
    }
    
    // Преобразуем десятичное число в целевую систему счисления
    QString result = QString::number(decimal, toBase);
    return result.toUpper(); // Возвращаем результат в верхнем регистре для HEX
} 