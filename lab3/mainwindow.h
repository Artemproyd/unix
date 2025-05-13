#ifndef MAINWINDOW_H
#define MAINWINDOW_H

#include <QMainWindow>
#include <QVector>
#include <QTimer>
#include <QComboBox>
#include <QPushButton>
#include <QSlider>
#include <QLabel>
#include <QSpinBox>
#include <QGraphicsScene>
#include <QGraphicsView>
#include <QGraphicsRectItem>
#include <QVBoxLayout>
#include <QHBoxLayout>
#include <QGroupBox>

class MainWindow : public QMainWindow
{
    Q_OBJECT

public:
    MainWindow(QWidget *parent = nullptr);
    ~MainWindow();

private slots:
    void startSorting();
    void resetArray();
    void updateArraySize(int size);
    void updateSortingSpeed(int speed);
    void sortingStep();
    void algorithmChanged(int index);

private:
    // UI элементы
    QComboBox *algorithmComboBox;
    QPushButton *startButton;
    QPushButton *resetButton;
    QSlider *sizeSlider;
    QSpinBox *sizeSpinBox;
    QSlider *speedSlider;
    QLabel *speedLabel;
    QLabel *operationsLabel;
    QLabel *timeLabel;
    QGraphicsScene *scene;
    QGraphicsView *view;
    QLabel *arrayLabel;
    
    // Данные для сортировки
    QVector<int> array;
    QVector<QGraphicsRectItem*> bars;
    QTimer *timer;
    
    // Переменные состояния (в том же порядке, что и в инициализации)
    int currentStep;
    int operations;
    bool sorting;
    
    int arraySize;
    int sortingSpeed;
    
    // Индексы для алгоритмов сортировки
    int i, j;
    
    // Текущий алгоритм
    enum Algorithm {
        BUBBLE_SORT,
        SELECTION_SORT,
        INSERTION_SORT,
        QUICK_SORT,
        MERGE_SORT
    };
    Algorithm currentAlgorithm;
    
    // Методы
    void setupUi();
    void generateRandomArray();
    void drawArray();
    void updateArray();
    void highlightBars(int i, int j, QColor color);
    void swapBars(int i, int j);
    
    // Алгоритмы сортировки
    void bubbleSortStep();
    void selectionSortStep();
    void insertionSortStep();
    void quickSortStep();
    void mergeSortStep();
    
    // Вспомогательные переменные для быстрой сортировки
    QVector<int> quickSortStack;
    
    // Вспомогательные переменные для сортировки слиянием
    QVector<QVector<int>> mergeSortRuns;
    int currentMergeStep;
    
    // Метод для завершения сортировки
    void finishSorting();
};

#endif 