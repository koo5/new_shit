#ifndef MAINWINDOW_H
#define MAINWINDOW_H

#include <jcon/json_rpc_tcp_client.h>

#include <QMainWindow>
#include <QTimer>

namespace Ui {
class MainWindow;
}

class MainWindow : public QMainWindow
{
	Q_OBJECT

public:
	explicit MainWindow(QWidget *parent = 0);
	~MainWindow();

private slots:
	void on_textEdit_textChanged();

private:
	QTimer menu_fetcher_timer;
	Ui::MainWindow *ui;
	jcon::JsonRpcTcpClient *client;
	void addNewlyReceivedMenuItem(const QString &text);
	void fetch_new_menu_items();
};

#endif // MAINWINDOW_H
