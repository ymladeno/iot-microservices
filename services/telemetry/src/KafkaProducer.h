#pragma once

#include <librdkafka/rdkafka.h>

#include <string>

class KafkaProducer {
  public:
    explicit KafkaProducer(const std::string& brokers);
    ~KafkaProducer();

    bool publish(const std::string& json);

  private:
    rd_kafka_t* producer_ = nullptr;
};
