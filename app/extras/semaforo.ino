#include <Wire.h>
#include <hd44780.h>
#include <hd44780ioClass/hd44780_I2Cexp.h>

const int ledVerde1 = 2;
const int ledVerde2 = 3;
const int ledVerde3 = 4;
const int ledVerde4 = 5;

const int ledAmarillo1 = 6;
const int ledAmarillo2 = 7;
const int ledAmarillo3 = 8;
const int ledAmarillo4 = 9;

const int ledRojo1 = 10;
const int ledRojo2 = 11;
const int ledRojo3 = 12;
const int ledRojo4 = 13;

const int alertaSonora = A2;

hd44780_I2Cexp lcd;

const int ATENCION_BAJA  = 0;
const int ATENCION_MEDIA = 1;
const int ATENCION_ALTA  = 2;

int nivelAtencionAnterior = -1;

unsigned long ultimoDatoMillis = 0;
const unsigned long TIMEOUT_MS = 5000;
bool datoValido = false;


void setLuzVerde(int estado){
  digitalWrite(ledVerde1, estado);
  digitalWrite(ledVerde2, estado);
  digitalWrite(ledVerde3, estado);
  digitalWrite(ledVerde4, estado);
}


void setLuzAmarilla(int estado){
  digitalWrite(ledAmarillo1, estado);
  digitalWrite(ledAmarillo2, estado);
  digitalWrite(ledAmarillo3, estado);
  digitalWrite(ledAmarillo4, estado);
}


void setLuzRoja(int estado){
  digitalWrite(ledRojo1, estado);
  digitalWrite(ledRojo2, estado);
  digitalWrite(ledRojo3, estado);
  digitalWrite(ledRojo4, estado);
}


void apagarLeds() {
  setLuzVerde(LOW);
  setLuzAmarilla(LOW);
  setLuzRoja(LOW);
}


void setup() {
  pinMode(ledVerde1, OUTPUT);
  pinMode(ledVerde2, OUTPUT);
  pinMode(ledVerde3, OUTPUT);
  pinMode(ledVerde4, OUTPUT);

  pinMode(ledAmarillo1, OUTPUT);
  pinMode(ledAmarillo2, OUTPUT);
  pinMode(ledAmarillo3, OUTPUT);
  pinMode(ledAmarillo4, OUTPUT);

  pinMode(ledRojo1, OUTPUT);
  pinMode(ledRojo2, OUTPUT);
  pinMode(ledRojo3, OUTPUT);
  pinMode(ledRojo4, OUTPUT);

  pinMode(alertaSonora, OUTPUT);

  Serial.begin(115200);

  lcd.begin(16, 2);
  lcd.backlight();

  setLuzVerde(HIGH);
  setLuzAmarilla(HIGH);
  setLuzRoja(HIGH);

  lcd.clear();
  lcd.setCursor(0, 0);
  lcd.print("FOCUS METER:");
  lcd.setCursor(0, 1);
  lcd.print("Sin datos...");

  delay(3000);
  apagarLeds();
}


void loop() {
  unsigned long ahora = millis();

  if (Serial.available()) {
    String dato = Serial.readStringUntil('\n');
    dato.trim();

    if (dato.startsWith("<") && dato.endsWith(">")) {
      dato = dato.substring(1, dato.length() - 1);
      float valor = dato.toFloat();

      if (valor >= 0.0 && valor <= 100.0) {
        ultimoDatoMillis = ahora;
        datoValido = true;

        int nivelAtencionActual;

        if (valor >= 80.0) {
          setLuzVerde(HIGH);
          setLuzAmarilla(LOW);
          setLuzRoja(LOW);
          nivelAtencionActual = ATENCION_ALTA;

        } else if (valor >= 70.0) {
          setLuzVerde(LOW);
          setLuzAmarilla(HIGH);
          setLuzRoja(LOW);
          nivelAtencionActual = ATENCION_MEDIA;

        } else {
          setLuzVerde(LOW);
          setLuzAmarilla(LOW);
          setLuzRoja(HIGH);
          nivelAtencionActual = ATENCION_BAJA;
        }

        lcd.clear();
        lcd.setCursor(0, 0);
        lcd.print("Estimacion de");
        lcd.setCursor(0, 1);
        lcd.print("atencion: ");
        lcd.print(valor, 1);
        lcd.print("%");

        if (nivelAtencionActual != nivelAtencionAnterior) {
          tone(alertaSonora, 2000, 200);
          nivelAtencionAnterior = nivelAtencionActual;
        }
      }
    }
  }

  if (datoValido && (ahora - ultimoDatoMillis > TIMEOUT_MS)) {
    apagarLeds();
    lcd.clear();
    lcd.setCursor(0, 0);
    lcd.print("FOCUS METER:");
    lcd.setCursor(0, 1);
    lcd.print("Sin datos...");
    datoValido = false;
    nivelAtencionAnterior = -1;
  }
}