#include "KafkaProducer.h"

#include <iostream>
#include <stdexcept>

KafkaProducer::KafkaProducer(const std::string& brokers) {
    char errstr[512];

    rd_kafka_conf_t* conf = rd_kafka_conf_new();

    if (rd_kafka_conf_set(conf, "bootstrap.servers", brokers.c_str(),
                          errstr, sizeof(errstr)) != RD_KAFKA_CONF_OK) {
        rd_kafka_conf_destroy(conf);
        throw std::runtime_error(errstr);
    }

    producer_ =
        rd_kafka_new(RD_KAFKA_PRODUCER, conf, errstr, sizeof(errstr));

    if (!producer_) {
        throw std::runtime_error(errstr);
    }
}

KafkaProducer::~KafkaProducer() {
    if (producer_) {
        rd_kafka_flush(producer_, 5000);
        rd_kafka_destroy(producer_);
    }
}

bool KafkaProducer::publish(const std::string& json) {
    rd_kafka_resp_err_t err = rd_kafka_producev(
        producer_, RD_KAFKA_V_TOPIC("measurements"),
        RD_KAFKA_V_VALUE(const_cast<char*>(json.data()), json.size()),
        RD_KAFKA_V_END);

    if (err != RD_KAFKA_RESP_ERR_NO_ERROR) {
        std::cerr << "Kafka publish failed: " << rd_kafka_err2str(err)
                  << '\n';
        return false;
    }

    // Wait for Kafka delivery acknowledgment.
    // This simple learning implementation flushes each message.
    err = rd_kafka_flush(producer_, 5000);

    if (err != RD_KAFKA_RESP_ERR_NO_ERROR) {
        std::cerr << "Kafka delivery timed out\n";
        return false;
    }

    return true;
}
