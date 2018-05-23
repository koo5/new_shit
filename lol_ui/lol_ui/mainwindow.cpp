#include <QMessageBox>
#include <QDebug>

#include "mainwindow.h"
#include "ui_mainwindow.h"

MainWindow::MainWindow(QWidget *parent) :
	QMainWindow(parent),
	ui(new Ui::MainWindow)
{
	ui->setupUi(this);

	client = new jcon::JsonRpcTcpClient(this);
	int port = 9999;
	const QString host = "127.0.0.1";
	while(true)
	{
		if (!client->connectToServer(host, port))
		{
			port++;
			if (port > 10020)
			{
			   QMessageBox::critical(this, "not connected", "not connected");
			   return;
			}
		}
		else
		{
		   qInfo() << QStringLiteral("connected to %0:%1").arg(host).arg(port);
		   break;
		}
	}


	on_textEdit_textChanged();

	menu_fetcher_timer.start(200);
	connect() menu_fetcher_timer
	fetch_new_menu_items()

}

MainWindow::~MainWindow()
{
	delete ui;
}

void MainWindow::fetch_new_menu_items()
{
	req->connect(req.get(), &jcon::JsonRpcRequest::result,
				 [this](const QVariant& result)
	{
		addNewlyReceivedMenuItems(result.toString());
	});
}

void MainWindow::addNewlyReceivedMenuItems(QVariant &items)
{
	addNewlyReceivedMenuItem("xx")
}

void MainWindow::addNewlyReceivedMenuItem(const QString& text)
{
	ui->listWidget->addItem(text);
}

void MainWindow::on_textEdit_textChanged()
{
	client->callAsync("setReplPromptText", ui->textEdit->toPlainText());
	client->callAsync("makeMenu");
}
