FROM bedasoftware/fhirsnake as seeds_builder

ADD resources/seeds /app/resources

RUN mkdir /output
RUN /app/entrypoint.sh export --output /output/seeds.ndjson.gz

FROM eclipse-temurin:17 AS builder

RUN apt-get update && apt-get install -y git

RUN mkdir /opt/zen
RUN wget -O /opt/zen/zen.jar https://github.com/HealthSamurai/ftr/releases/latest/download/zen.jar
   
RUN mkdir /opt/app
RUN mkdir /opt/app/zenproject

COPY --from=seeds_builder /output/seeds.ndjson.gz /opt/app/zenproject/seeds.ndjson.gz

WORKDIR /opt/app

ADD zenproject/zen-package.edn /opt/app/zenproject/zen-package.edn
RUN cd /opt/app/zenproject && java -jar /opt/zen/zen.jar zen pull-deps

ADD zenproject /opt/app/zenproject
RUN cd /opt/app && java -jar /opt/zen/zen.jar zen build zenproject zen-package

RUN ls -lah /opt/app/zenproject

FROM bash AS runner

RUN mkdir /app
WORKDIR /app

COPY --from=builder /opt/app/zenproject/zen-package.zip /app/zen-package.zip

CMD ["cp", "/app/zen-package.zip", "/output/zen-package.zip"]
