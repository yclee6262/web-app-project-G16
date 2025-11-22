-- 使用由 docker-compose 自動建立的資料庫
USE `investment_platform`;
SET NAMES utf8mb4;

-- ----------------------------
-- 表 1: Users (使用 Username 和 Password Hash)
-- ----------------------------
CREATE TABLE Users (
    `user_id` INT AUTO_INCREMENT PRIMARY KEY,
    `username` VARCHAR(100) NOT NULL UNIQUE,
    `password_hash` VARCHAR(255) NOT NULL,
    `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ----------------------------
-- 表 2: Securities (不變)
-- ----------------------------
CREATE TABLE Securities (
    `ticker_symbol` VARCHAR(20) NOT NULL PRIMARY KEY,
    `name` VARCHAR(255) NOT NULL,
    `exchange` VARCHAR(50)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ----------------------------
-- 表 3: HistoricalPrices (不變)
-- ----------------------------
CREATE TABLE HistoricalPrices (
    `ticker_symbol` VARCHAR(20) NOT NULL,
    `date` DATE NOT NULL,
    `close` DECIMAL(10, 4) NOT NULL,
    `adjusted_close` DECIMAL(10, 4) NOT NULL,
    `volume` BIGINT NOT NULL,
    PRIMARY KEY (`ticker_symbol`, `date`),
    FOREIGN KEY (`ticker_symbol`) REFERENCES Securities(`ticker_symbol`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ----------------------------
-- 表 4: Portfolios (更新)
-- ----------------------------
CREATE TABLE Portfolios (
    `portfolio_id` INT AUTO_INCREMENT PRIMARY KEY,
    `user_id` INT NOT NULL, -- 【更新】關聯到 INT 型的 user_id
    `name` VARCHAR(100) NOT NULL,
    `updated_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX `idx_user_id` (`user_id`),
    FOREIGN KEY (`user_id`) REFERENCES Users(`user_id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ----------------------------
-- 表 5: PortfolioItems (更新)
-- ----------------------------
-- (註：我將保留我們之前的 "quantity" 設計，
--  因為 docs/portfolio.md 也顯示 "quantity"。)
CREATE TABLE PortfolioItems (
    `item_id` INT AUTO_INCREMENT PRIMARY KEY,
    `portfolio_id` INT NOT NULL,
    `ticker_symbol` VARCHAR(20) NOT NULL,
    `quantity` DECIMAL(14, 6) NOT NULL, 
    FOREIGN KEY (`portfolio_id`) REFERENCES Portfolios(`portfolio_id`) ON DELETE CASCADE,
    FOREIGN KEY (`ticker_symbol`) REFERENCES Securities(`ticker_symbol`),
    UNIQUE KEY `uk_portfolio_security` (`portfolio_id`, `ticker_symbol`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ----------------------------
-- 表 6: WatchListItems (新增)
-- ----------------------------
-- 儲存使用者的關注清單
CREATE TABLE WatchListItems (
    `user_id` INT NOT NULL,
    `ticker_symbol` VARCHAR(20) NOT NULL,
    `added_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- 複合主鍵：確保同一個使用者對同一支股票只能關注一次
    PRIMARY KEY (`user_id`, `ticker_symbol`),
    
    -- 外鍵關聯
    FOREIGN KEY (`user_id`) REFERENCES Users(`user_id`) ON DELETE CASCADE,
    FOREIGN KEY (`ticker_symbol`) REFERENCES Securities(`ticker_symbol`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;