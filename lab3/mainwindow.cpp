#include "mainwindow.h"
#include <QHeaderView>
#include <QMessageBox>
#include <QFile>
#include <QDir>
#include <QTextStream>
#include <QTime>
#include <QRandomGenerator>
#include <QElapsedTimer>

MainWindow::MainWindow(QWidget *parent)
    : QMainWindow(parent), 
      currentStep(0), 
      operations(0), 
      sorting(false)
{
    setupUi();
    
    // Инициализация таймера
    timer = new QTimer(this);
    connect(timer, &QTimer::timeout, this, &MainWindow::sortingStep);
    
    // Начальные значения
    arraySize = 50;
    sortingSpeed = 50;
    currentAlgorithm = BUBBLE_SORT;
    
    // Генерация начального массива
    generateRandomArray();
    drawArray();
}

MainWindow::~MainWindow()
{
}

void MainWindow::setupUi()
{
    // Создаем центральный виджет и главный layout
    QWidget *centralWidget = new QWidget(this);
    QVBoxLayout *mainLayout = new QVBoxLayout(centralWidget);
    
    // Группа управления
    QGroupBox *controlGroup = new QGroupBox("Управление", this);
    QVBoxLayout *controlLayout = new QVBoxLayout(controlGroup);
    
    // Выбор алгоритма
    QHBoxLayout *algorithmLayout = new QHBoxLayout();
    QLabel *algorithmLabel = new QLabel("Алгоритм:", this);
    algorithmComboBox = new QComboBox(this);
    algorithmComboBox->addItem("Сортировка пузырьком");
    algorithmComboBox->addItem("Сортировка выбором");
    algorithmComboBox->addItem("Сортировка вставками");
    algorithmComboBox->addItem("Быстрая сортировка");
    algorithmComboBox->addItem("Сортировка слиянием");
    algorithmLayout->addWidget(algorithmLabel);
    algorithmLayout->addWidget(algorithmComboBox);
    
    // Размер массива
    QHBoxLayout *sizeLayout = new QHBoxLayout();
    QLabel *sizeLabel = new QLabel("Размер массива:", this);
    sizeSlider = new QSlider(Qt::Horizontal, this);
    sizeSlider->setRange(10, 200);
    sizeSlider->setValue(50);
    sizeSpinBox = new QSpinBox(this);
    sizeSpinBox->setRange(10, 200);
    sizeSpinBox->setValue(50);
    sizeLayout->addWidget(sizeLabel);
    sizeLayout->addWidget(sizeSlider);
    sizeLayout->addWidget(sizeSpinBox);
    
    // Скорость сортировки
    QHBoxLayout *speedLayout = new QHBoxLayout();
    QLabel *speedTextLabel = new QLabel("Скорость:", this);
    speedSlider = new QSlider(Qt::Horizontal, this);
    speedSlider->setRange(1, 100);
    speedSlider->setValue(50);
    speedLabel = new QLabel("50", this);
    speedLayout->addWidget(speedTextLabel);
    speedLayout->addWidget(speedSlider);
    speedLayout->addWidget(speedLabel);
    
    // Кнопки
    QHBoxLayout *buttonLayout = new QHBoxLayout();
    startButton = new QPushButton("Старт", this);
    resetButton = new QPushButton("Сброс", this);
    buttonLayout->addWidget(startButton);
    buttonLayout->addWidget(resetButton);
    
    // Статистика
    QHBoxLayout *statsLayout = new QHBoxLayout();
    operationsLabel = new QLabel("Операции: 0", this);
    timeLabel = new QLabel("Время: 0 мс", this);
    statsLayout->addWidget(operationsLabel);
    statsLayout->addWidget(timeLabel);
    
    // Добавляем метку для отображения массива
    arrayLabel = new QLabel(this);
    arrayLabel->setWordWrap(true);
    arrayLabel->setAlignment(Qt::AlignCenter);
    arrayLabel->setStyleSheet("font-family: monospace; font-size: 12px;");
    
    // Добавляем все в layout управления
    controlLayout->addLayout(algorithmLayout);
    controlLayout->addLayout(sizeLayout);
    controlLayout->addLayout(speedLayout);
    controlLayout->addLayout(buttonLayout);
    controlLayout->addLayout(statsLayout);
    
    // Создаем сцену для визуализации
    scene = new QGraphicsScene(this);
    view = new QGraphicsView(scene, this);
    view->setRenderHint(QPainter::Antialiasing);
    view->setMinimumHeight(300);
    
    // Добавляем пояснение к графику
    QLabel *graphExplanation = new QLabel("График: высота столбца соответствует значению элемента массива", this);
    graphExplanation->setAlignment(Qt::AlignCenter);
    
    // Добавляем все в главный layout
    mainLayout->addWidget(controlGroup);
    mainLayout->addWidget(graphExplanation); // Добавляем пояснение
    mainLayout->addWidget(view);
    mainLayout->addWidget(arrayLabel);
    
    // Устанавливаем центральный виджет
    setCentralWidget(centralWidget);
    
    // Устанавливаем заголовок окна и размеры
    setWindowTitle("Визуализатор алгоритмов сортировки");
    resize(800, 600);
    
    // Подключаем сигналы к слотам
    connect(startButton, &QPushButton::clicked, this, &MainWindow::startSorting);
    connect(resetButton, &QPushButton::clicked, this, &MainWindow::resetArray);
    connect(sizeSlider, &QSlider::valueChanged, sizeSpinBox, &QSpinBox::setValue);
    connect(sizeSpinBox, QOverload<int>::of(&QSpinBox::valueChanged), sizeSlider, &QSlider::setValue);
    connect(sizeSlider, &QSlider::valueChanged, this, &MainWindow::updateArraySize);
    connect(speedSlider, &QSlider::valueChanged, this, &MainWindow::updateSortingSpeed);
    connect(algorithmComboBox, QOverload<int>::of(&QComboBox::currentIndexChanged), 
            this, &MainWindow::algorithmChanged);
}

void MainWindow::generateRandomArray()
{
    array.resize(arraySize);
    for (int i = 0; i < arraySize; ++i) {
        array[i] = QRandomGenerator::global()->bounded(10, 100);
    }
}

void MainWindow::drawArray()
{
    scene->clear();
    bars.clear();
    
    // Определяем размеры сцены
    int sceneWidth = view->width() - 20;
    int sceneHeight = view->height() - 20;
    scene->setSceneRect(0, 0, sceneWidth, sceneHeight);
    
    // Ограничиваем максимальное количество отображаемых элементов для лучшей видимости
    int visibleElements = qMin(arraySize, 50); // Показываем максимум 50 элементов
    
    // Определяем ширину столбца с небольшим отступом между столбцами
    double barWidth = static_cast<double>(sceneWidth) / visibleElements * 0.8; // 80% от доступной ширины
    double spacing = static_cast<double>(sceneWidth) / visibleElements * 0.2; // 20% для отступа
    
    // Находим максимальное значение для масштабирования
    int maxValue = *std::max_element(array.begin(), array.end());
    double scale = static_cast<double>(sceneHeight) / maxValue;
    
    // Создаем столбцы с толстыми рамками
    QPen thickPen(Qt::black);
    thickPen.setWidth(2); // Толщина рамки
    
    for (int i = 0; i < arraySize; ++i) {
        double height = array[i] * scale;
        QGraphicsRectItem *bar = scene->addRect(
            i * (barWidth + spacing), // Добавляем отступ между столбцами
            sceneHeight - height, 
            barWidth, 
            height, 
            thickPen, // Используем толстую рамку
            QBrush(Qt::blue)
        );
        bars.append(bar);
    }
}

void MainWindow::updateArray()
{
    // Обновляем высоту столбцов
    int sceneHeight = view->height() - 20;
    int maxValue = *std::max_element(array.begin(), array.end());
    double scale = static_cast<double>(sceneHeight) / maxValue;
    
    int visibleElements = qMin(arraySize, 50);
    double barWidth = static_cast<double>(scene->width()) / visibleElements * 0.8;
    double spacing = static_cast<double>(scene->width()) / visibleElements * 0.2;
    
    for (int i = 0; i < arraySize && i < bars.size(); ++i) {
        double height = array[i] * scale;
        bars[i]->setRect(
            i * (barWidth + spacing),
            sceneHeight - height,
            barWidth,
            height
        );
    }
    
    // Обновляем текстовое представление массива
    QString arrayText = "Массив: [ ";
    for (int i = 0; i < arraySize; ++i) {
        arrayText += QString::number(array[i]);
        if (i < arraySize - 1) {
            arrayText += ", ";
        }
        
        // Добавляем перенос строки каждые 15 элементов для лучшей читаемости
        if ((i + 1) % 15 == 0 && i < arraySize - 1) {
            arrayText += "\n";
        }
    }
    arrayText += " ]";
    arrayLabel->setText(arrayText);
}

void MainWindow::highlightBars(int i, int j, QColor color)
{
    // Сбрасываем цвет всех столбцов
    QPen thickPen(Qt::black);
    thickPen.setWidth(2);
    
    for (auto bar : bars) {
        bar->setBrush(QBrush(Qt::blue));
        bar->setPen(thickPen);
    }
    
    // Выделяем нужные столбцы
    QPen highlightPen(color.darker());
    highlightPen.setWidth(3); // Еще более толстая рамка для выделенных элементов
    
    if (i >= 0 && i < bars.size()) {
        bars[i]->setBrush(QBrush(color));
        bars[i]->setPen(highlightPen);
    }
    
    if (j >= 0 && j < bars.size()) {
        bars[j]->setBrush(QBrush(color));
        bars[j]->setPen(highlightPen);
    }
    
    // Обновляем текстовое представление
    QString arrayText = "Массив: [ ";
    for (int k = 0; k < arraySize; ++k) {
        arrayText += QString::number(array[k]);
        if (k < arraySize - 1) {
            arrayText += ", ";
        }
        
        // Добавляем перенос строки каждые 15 элементов для лучшей читаемости
        if ((k + 1) % 15 == 0 && k < arraySize - 1) {
            arrayText += "\n";
        }
    }
    arrayText += " ]";
    
    // Добавляем информацию о сравниваемых элементах
    if (i >= 0 && j >= 0 && i < arraySize && j < arraySize) {
        arrayText += "\nСравниваем элементы: " + QString::number(array[i]) + " и " + QString::number(array[j]);
    }
    
    arrayLabel->setText(arrayText);
}

void MainWindow::swapBars(int i, int j)
{
    // Меняем элементы массива местами
    std::swap(array[i], array[j]);
    
    // Обновляем отображение
    int sceneHeight = view->height() - 20;
    int maxValue = *std::max_element(array.begin(), array.end());
    double scale = static_cast<double>(sceneHeight) / maxValue;
    
    int visibleElements = qMin(arraySize, 50);
    double barWidth = static_cast<double>(scene->width()) / visibleElements * 0.8;
    double spacing = static_cast<double>(scene->width()) / visibleElements * 0.2;
    
    // Обновляем высоту столбцов
    double height1 = array[i] * scale;
    double height2 = array[j] * scale;
    
    // Используем толстую рамку
    QPen thickPen(Qt::black);
    thickPen.setWidth(2);
    
    bars[i]->setRect(
        i * (barWidth + spacing),
        sceneHeight - height1,
        barWidth,
        height1
    );
    bars[i]->setPen(thickPen);
    
    bars[j]->setRect(
        j * (barWidth + spacing),
        sceneHeight - height2,
        barWidth,
        height2
    );
    bars[j]->setPen(thickPen);
    
    // Выделяем обмененные элементы
    bars[i]->setBrush(QBrush(Qt::red));
    bars[j]->setBrush(QBrush(Qt::red));
    
    // Обновляем текстовое представление
    QString arrayText = "Массив: [ ";
    for (int k = 0; k < arraySize; ++k) {
        arrayText += QString::number(array[k]);
        if (k < arraySize - 1) {
            arrayText += ", ";
        }
        
        // Добавляем перенос строки каждые 15 элементов для лучшей читаемости
        if ((k + 1) % 15 == 0 && k < arraySize - 1) {
            arrayText += "\n";
        }
    }
    arrayText += " ]";
    arrayText += "\nПоменяли местами: " + QString::number(array[i]) + " и " + QString::number(array[j]);
    arrayLabel->setText(arrayText);
}

void MainWindow::startSorting()
{
    if (!sorting) {
        // Начинаем сортировку
        sorting = true;
        startButton->setText("Пауза");
        
        // Сбрасываем счетчики
        operations = 0;
        currentStep = 0;
        
        // Инициализируем индексы для алгоритмов
        i = 0;
        j = 0;
        
        // Инициализация для быстрой сортировки
        if (currentAlgorithm == QUICK_SORT) {
            quickSortStack.clear();
            quickSortStack.append(0);
            quickSortStack.append(arraySize - 1);
        }
        
        // Инициализация для сортировки слиянием
        if (currentAlgorithm == MERGE_SORT) {
            mergeSortRuns.clear();
            for (int i = 0; i < arraySize; ++i) {
                QVector<int> run;
                run.append(array[i]);
                mergeSortRuns.append(run);
            }
            currentMergeStep = 0;
        }
        
        // Запускаем таймер
        timer->setInterval(1000 / sortingSpeed);
        timer->start();
    } else {
        // Приостанавливаем сортировку
        sorting = false;
        startButton->setText("Продолжить");
        timer->stop();
    }
}

void MainWindow::resetArray()
{
    // Останавливаем сортировку, если она запущена
    if (sorting) {
        sorting = false;
        startButton->setText("Старт");
        timer->stop();
    }
    
    // Генерируем новый массив
    generateRandomArray();
    drawArray();
    
    // Сбрасываем счетчики
    operations = 0;
    operationsLabel->setText("Операции: 0");
    timeLabel->setText("Время: 0 мс");
}

void MainWindow::updateArraySize(int size)
{
    // Обновляем размер массива
    arraySize = size;
    
    // Если сортировка не запущена, обновляем массив
    if (!sorting) {
        resetArray();
    }
}

void MainWindow::updateSortingSpeed(int speed)
{
    // Обновляем скорость сортировки
    sortingSpeed = speed;
    speedLabel->setText(QString::number(speed));
    
    // Обновляем интервал таймера
    timer->setInterval(1000 / speed);
}

void MainWindow::algorithmChanged(int index)
{
    // Обновляем текущий алгоритм
    currentAlgorithm = static_cast<Algorithm>(index);
    
    // Если сортировка запущена, останавливаем её
    if (sorting) {
        sorting = false;
        startButton->setText("Старт");
        timer->stop();
        resetArray();
    }
}

void MainWindow::sortingStep()
{
    // Выполняем шаг сортировки в зависимости от выбранного алгоритма
    switch (currentAlgorithm) {
        case BUBBLE_SORT:
            bubbleSortStep();
            break;
        case SELECTION_SORT:
            selectionSortStep();
            break;
        case INSERTION_SORT:
            insertionSortStep();
            break;
        case QUICK_SORT:
            quickSortStep();
            break;
        case MERGE_SORT:
            mergeSortStep();
            break;
    }
    
    // Обновляем статистику
    operationsLabel->setText("Операции: " + QString::number(operations));
}

void MainWindow::bubbleSortStep()
{
    if (i < arraySize - 1) {
        if (j < arraySize - i - 1) {
            // Выделяем сравниваемые элементы с правильными параметрами
            highlightBars(j, j + 1, Qt::yellow);
            
            // Сравниваем и меняем местами, если нужно
            operations++;
            if (array[j] > array[j + 1]) {
                swapBars(j, j + 1);
            }
            
            // Переходим к следующей паре
            j++;
        } else {
            // Переходим к следующему проходу
            j = 0;
            i++;
            
            // Обновляем отображение после каждого прохода
            updateArray();
        }
    } else {
        // Сортировка завершена
        sorting = false;
        startButton->setText("Старт");
        timer->stop();
        
        // Выделяем все столбцы зеленым, показывая завершение
        QPen thickPen(Qt::black);
        thickPen.setWidth(2);
        
        for (auto bar : bars) {
            bar->setBrush(QBrush(Qt::green));
            bar->setPen(thickPen);
        }
    }
}

void MainWindow::selectionSortStep()
{
    if (i < arraySize - 1) {
        if (j == i) {
            // Начинаем новый проход, ищем минимальный элемент
            j = i + 1;
            currentStep = i; // Индекс текущего минимума
            highlightBars(currentStep, -1, Qt::yellow);
            operations++;
        } else if (j < arraySize) {
            // Сравниваем текущий элемент с минимальным
            highlightBars(currentStep, j, Qt::green);
            operations++;
            
            if (array[j] < array[currentStep]) {
                currentStep = j;
                highlightBars(currentStep, -1, Qt::yellow);
            }
            
            j++;
        } else {
            // Завершаем проход, меняем местами найденный минимум и текущий элемент
            if (currentStep != i) {
                swapBars(i, currentStep);
            }
            
            i++;
            j = i;
        }
    } else {
        // Сортировка завершена
        sorting = false;
        startButton->setText("Старт");
        timer->stop();
        
        // Выделяем все столбцы зеленым, показывая завершение
        for (auto bar : bars) {
            bar->setBrush(QBrush(Qt::green));
        }
    }
}

void MainWindow::insertionSortStep()
{
    if (i < arraySize) {
        if (i == 0) {
            // Первый элемент уже отсортирован
            i++;
            j = i;
        } else if (j > 0 && array[j - 1] > array[j]) {
            // Сдвигаем элемент влево, пока не найдем правильную позицию
            highlightBars(j, j - 1, Qt::green);
            swapBars(j, j - 1);
            j--;
        } else {
            // Переходим к следующему элементу
            i++;
            j = i;
        }
    } else {
        // Сортировка завершена
        sorting = false;
        startButton->setText("Старт");
        timer->stop();
        
        // Выделяем все столбцы зеленым, показывая завершение
        for (auto bar : bars) {
            bar->setBrush(QBrush(Qt::green));
        }
    }
}

void MainWindow::quickSortStep()
{
    if (!quickSortStack.isEmpty()) {
        // Извлекаем границы текущего подмассива
        int high = quickSortStack.takeLast();
        int low = quickSortStack.takeLast();
        
        // Если подмассив имеет более одного элемента
        if (low < high) {
            // Выбираем опорный элемент (последний)
            int pivot = array[high];
            highlightBars(high, -1, Qt::yellow);
            
            // Индекс для элементов меньше опорного
            int i = low - 1;
            
            // Проходим по подмассиву
            for (int j = low; j < high; j++) {
                highlightBars(j, high, Qt::green);
                operations++;
                
                // Если текущий элемент меньше опорного
                if (array[j] < pivot) {
                    i++;
                    swapBars(i, j);
                }
            }
            
            // Помещаем опорный элемент на правильную позицию
            swapBars(i + 1, high);
            
            // Получаем индекс опорного элемента
            int pivotIndex = i + 1;
            
            // Добавляем границы подмассивов в стек
            quickSortStack.append(low);
            quickSortStack.append(pivotIndex - 1);
            
            quickSortStack.append(pivotIndex + 1);
            quickSortStack.append(high);
        }
    } else {
        // Сортировка завершена
        sorting = false;
        startButton->setText("Старт");
        timer->stop();
        
        // Выделяем все столбцы зеленым, показывая завершение
        for (auto bar : bars) {
            bar->setBrush(QBrush(Qt::green));
        }
    }
}

void MainWindow::mergeSortStep()
{
    // Если остался только один подмассив, сортировка завершена
    if (mergeSortRuns.size() == 1 && mergeSortRuns[0].size() == arraySize) {
        sorting = false;
        startButton->setText("Старт");
        timer->stop();
        
        // Выделяем все столбцы зеленым, показывая завершение
        for (auto bar : bars) {
            bar->setBrush(QBrush(Qt::green));
        }
        return;
    }
    
    // Если есть хотя бы два подмассива, сливаем их
    if (mergeSortRuns.size() >= 2) {
        // Берем два подмассива
        QVector<int> left = mergeSortRuns.takeFirst();
        QVector<int> right = mergeSortRuns.takeFirst();
        
        // Сливаем их
        QVector<int> merged;
        int i = 0, j = 0;
        
        while (i < left.size() && j < right.size()) {
            operations++;
            if (left[i] <= right[j]) {
                merged.append(left[i++]);
            } else {
                merged.append(right[j++]);
            }
        }
        
        // Добавляем оставшиеся элементы
        while (i < left.size()) {
            merged.append(left[i++]);
        }
        
        while (j < right.size()) {
            merged.append(right[j++]);
        }
        
        // Добавляем слитый подмассив обратно в список
        mergeSortRuns.append(merged);
        
        // Обновляем исходный массив для визуализации
        int startIndex = 0;
        for (const auto& run : mergeSortRuns) {
            for (int val : run) {
                array[startIndex++] = val;
            }
        }
        
        updateArray();
        
        // Выделяем текущий слитый подмассив
        int endIndex = startIndex - 1;
        startIndex = endIndex - merged.size() + 1;
        for (int k = startIndex; k <= endIndex; k++) {
            if (k < bars.size()) {
                bars[k]->setBrush(QBrush(Qt::green));
            }
        }
    }
} 
