# 🎴 遊戯王ニュース自動監視システム  
**AWS Lambda × EC2 プロキシ × Playwright × Discord Webhook**

Cloudflare で保護された「遊戯王.jp」を安定してスクレイピングし、  
新規情報を Discord に自動通知するためのシステム構築手順をまとめたドキュメントです。

---

## 📌 概要

このシステムは以下を自動化します：

- EC2（日本 IP）をプロキシとして起動  
- Playwright（Chromium）で Cloudflare を突破  
- 遊戯王公式サイトをスクレイピング  
- 新規情報を Discord に通知  
- EC2 を停止  
- EventBridge で **毎日 12:02 / 21:02（JST）** に実行

Lambda 単体では Cloudflare に弾かれるため、  
**EC2 プロキシ（Squid）を経由する構成**を採用しています。

---

## 🏗 アーキテクチャ




---

## 🖥 EC2 プロキシサーバー構築

### 1. EC2 作成

- Amazon Linux 2023
- Elastic IP を割り当てる
- セキュリティグループで **3128/TCP** を開放（テスト時のみ 0.0.0.0/0）

### 2. Squid インストール

```bash
sudo dnf install -y squid
sudo systemctl enable squid
sudo systemctl start squid
```

### 3.外部アクセス許可
/etc/squid/squid.conf に追加：
```
http_access allow all
http_access deny all

```

### 4. 動作確認
EC2内部
```
curl -x http://127.0.0.1:3128 https://example.com
```

外部
```
curl -x http://YOUR_EIP:3128 https://example.com
```


## 🛠 トラブルシューティング
❌ Lambda で EC2 起動失敗
→ IAM ロールに ec2:StartInstances が無い

❌ 外部からプロキシに接続できない
→ Squid の http_access allow all が未設定
→ SG の 3128 が閉じている

❌ Cloudflare に弾かれる
→ User-Agent / Accept-Language が必要
→ プロキシ経由になっていない可能性
