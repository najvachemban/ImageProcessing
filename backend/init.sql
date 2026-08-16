CREATE TABLE IF NOT EXISTS jobs (
    job_id          CHAR(36)      NOT NULL PRIMARY KEY,
    user_id         VARCHAR(64)   NOT NULL,
    filename        VARCHAR(255)  NOT NULL,
    operation       VARCHAR(32)   NOT NULL,
    parameters      JSON          NULL,
    status          VARCHAR(16)   NOT NULL DEFAULT 'PENDING',
    retry_count     INT           NOT NULL DEFAULT 0,
    error_message   TEXT          NULL,
    created_at      DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP,
    started_at      DATETIME      NULL,
    completed_at    DATETIME      NULL,

    INDEX idx_status (status),
    INDEX idx_user_id (user_id)
) ENGINE=InnoDB;