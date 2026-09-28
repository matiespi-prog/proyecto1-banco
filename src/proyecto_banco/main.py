def preprocesar_cuentas(cuentas_raw: list[dict]) -> list[dict]:
    cuentas_procesadas: list[dict] = []
    numeros_cuenta_vistos: set[int] = set()

    for item in cuentas_raw:
        if not isinstance(item, dict):
            continue

        if "titular" not in item or "numero_cuenta" not in item:
            continue
        if "saldo_inicial" not in item or "tipo" not in item:
            continue

        val_titular = item["titular"]
        val_numero = item["numero_cuenta"]
        val_saldo = item["saldo_inicial"]
        val_tipo = item["tipo"]

        if val_titular is None or val_numero is None:
            continue
        if val_saldo is None or val_tipo is None:
            continue

        try:
            val_titular_str = str(val_titular).strip()
            if not val_titular_str:
                continue
            palabras = val_titular_str.split()
            titular_limpio = " ".join([p.capitalize() for p in palabras])
        except Exception:
            continue

        try:
            numero_cuenta_limpio = int(str(val_numero).strip())
            if numero_cuenta_limpio in numeros_cuenta_vistos:
                continue
        except (ValueError, TypeError):
            continue

        try:
            saldo_inicial_limpio = int(str(val_saldo).strip())
            if saldo_inicial_limpio < 0:
                continue
        except (ValueError, TypeError):
            continue

        try:
            tipo_limpio = str(val_tipo).strip().lower()
            if tipo_limpio not in ("ahorro", "corriente"):
                continue
        except Exception:
            continue

        cuenta_dict: dict = {
            "titular": titular_limpio,
            "numero_cuenta": numero_cuenta_limpio,
            "saldo_inicial": saldo_inicial_limpio,
            "tipo": tipo_limpio,
        }

        if tipo_limpio == "ahorro":
            tasa = 0.5
            if "tasa_interes" in item and item["tasa_interes"] is not None:
                try:
                    tasa_candidata = float(str(item["tasa_interes"]).strip())
                    if tasa_candidata >= 0:
                        tasa = tasa_candidata
                except (ValueError, TypeError):
                    tasa = 0.5
            cuenta_dict["tasa_interes"] = tasa

        elif tipo_limpio == "corriente":
            limite = 100000
            if "limite_giro" in item and item["limite_giro"] is not None:
                try:
                    limite_candidato = int(str(item["limite_giro"]).strip())
                    if limite_candidato >= 0:
                        limite = limite_candidato
                except (ValueError, TypeError):
                    limite = 100000
            cuenta_dict["limite_giro"] = limite

        numeros_cuenta_vistos.add(numero_cuenta_limpio)
        cuentas_procesadas.append(cuenta_dict)

    return cuentas_procesadas


class Cuenta:

    def __init__(self, titular: str, numero_cuenta: int) -> None:
        self.titular = titular
        self.__numero_cuenta = int(numero_cuenta)
        self.__saldo = 0
        self.tipo_cuenta = "generica"

    def get_numero_cuenta(self) -> int:
        return self.__numero_cuenta

    def _set_saldo(self, nuevo_saldo: int) -> None:
        self.__saldo = nuevo_saldo

    def consultar_saldo(self) -> int:
        return self.__saldo

    def depositar(self, monto: int | float) -> int:
        if monto <= 0:
            raise ValueError("monto a depositar no valido tiene que ser positivo")
        self.__saldo += int(monto)
        return self.__saldo

    def girar(self, monto: int | float) -> int:
        if monto <= 0:
            raise ValueError("monto a girar no puede ser menor o igual a cero")
        if monto > self.__saldo:
            raise ValueError(f"no alcanza la plata saldo disponible {self.__saldo}")
        self.__saldo -= int(monto)
        return self.__saldo

    def obtener_informacion_basica(self) -> str:
        return f"Titular {self.titular} Cuenta {self.__numero_cuenta} Tipo {self.tipo_cuenta} Saldo {self.__saldo}"


class CuentaDeAhorro(Cuenta):

    def __init__(
        self, titular: str, numero_cuenta: int, tasa_interes: float = 0.5
    ) -> None:
        super().__init__(titular=titular, numero_cuenta=numero_cuenta)
        self.tipo_cuenta = "ahorro"
        if tasa_interes < 0:
            raise ValueError("tasa negativa no sirve")
        self.tasa_interes = float(tasa_interes)

    def aplicar_interes(self) -> int:
        saldo_actual = self.consultar_saldo()
        if saldo_actual > 0:
            interes = round(saldo_actual * (self.tasa_interes / 100.0))
            self.depositar(interes)
            return interes
        return 0

    def obtener_informacion_basica(self) -> str:
        return f"Cuenta Ahorro {self.get_numero_cuenta()} Titular {self.titular} Saldo {self.consultar_saldo()} Tasa {self.tasa_interes}"


class CuentaCorriente(Cuenta):

    def __init__(
        self, titular: str, numero_cuenta: int, limite_giro: int = 100000
    ) -> None:
        super().__init__(titular=titular, numero_cuenta=numero_cuenta)
        self.tipo_cuenta = "corriente"
        if limite_giro < 0:
            raise ValueError("limite de sobregiro no puede ser negativo")
        self.limite_giro = int(limite_giro)

    def girar(self, monto: int | float) -> int:
        if monto <= 0:
            raise ValueError("monto invalido")

        monto_int = int(monto)
        saldo_actual = self.consultar_saldo()

        if (saldo_actual - monto_int) < -self.limite_giro:
            disponible = saldo_actual + self.limite_giro
            raise ValueError(
                f"te pasaste del limite de sobregiro disponible total {disponible}"
            )

        self._set_saldo(saldo_actual - monto_int)
        return self.consultar_saldo()

    def obtener_informacion_basica(self) -> str:
        return f"Cuenta Corriente {self.get_numero_cuenta()} Titular {self.titular} Saldo {self.consultar_saldo()} Sobregiro {self.limite_giro}"


class Banco:

    def __init__(self, nombre: str) -> None:
        self.nombre = nombre
        self.cuentas: list[Cuenta] = []

    def abrir_cuenta(self, cuenta: Cuenta) -> bool:
        if not isinstance(cuenta, Cuenta):
            raise TypeError("objeto no es tipo cuenta")

        for c in self.cuentas:
            if c.get_numero_cuenta() == cuenta.get_numero_cuenta():
                raise ValueError(
                    f"la cuenta {cuenta.get_numero_cuenta()} ya esta registrada"
                )

        self.cuentas.append(cuenta)
        return True

    def buscar_cuenta(self, numero_cuenta: int) -> Cuenta | None:
        num = int(numero_cuenta)
        for c in self.cuentas:
            if c.get_numero_cuenta() == num:
                return c
        return None

    def transferir(
        self, numero_origen: int, numero_destino: int, monto: int | float
    ) -> bool:
        if monto <= 0:
            raise ValueError("monto de transferencia tiene que ser positivo")

        cuenta_origen = self.buscar_cuenta(numero_origen)
        if cuenta_origen is None:
            raise ValueError(f"cuenta origen {numero_origen} no existe")

        cuenta_destino = self.buscar_cuenta(numero_destino)
        if cuenta_destino is None:
            raise ValueError(f"cuenta destino {numero_destino} no existe")

        if (
            cuenta_origen.get_numero_cuenta()
            == cuenta_destino.get_numero_cuenta()
        ):
            raise ValueError("no puedes transferir a la misma cuenta")

        cuenta_origen.girar(monto)
        cuenta_destino.depositar(monto)
        return True

    def mostrar_cuentas(self) -> None:
        cuentas_ordenadas = sorted(
            self.cuentas, key=lambda c: c.get_numero_cuenta()
        )
        print(f"cuentas del banco {self.nombre}")
        if not cuentas_ordenadas:
            print("no hay cuentas registradas")
            return

        for c in cuentas_ordenadas:
            print(c.obtener_informacion_basica())


def main() -> None:
    print("revisando cuentas y limpiando")

    datos_brutos: list[dict] = [
        {
            "titular": "  ana pérez  ",
            "numero_cuenta": "1001",
            "saldo_inicial": "500000",
            "tipo": "ahorro",
            "tasa_interes": "1.2",
        },
        {
            "titular": "JUAN CARLOS OYARZÚN",
            "numero_cuenta": 1002,
            "saldo_inicial": 350000,
            "tipo": "corriente",
            "limite_giro": 200000,
        },
        {
            "titular": "patricio andrade",
            "numero_cuenta": " 1003 ",
            "saldo_inicial": "0",
            "tipo": "ahorro",
            "tasa_interes": "0.8",
        },
        {
            "titular": "Valeria Silva",
            "numero_cuenta": 1004,
            "saldo_inicial": 120000,
            "tipo": "corriente",
        },
        {
            "titular": "Camila Soto",
            "numero_cuenta": 1005,
            "saldo_inicial": 80000,
            "tipo": "ahorro",
        },
        {
            "titular": "Diego Ruiz",
            "numero_cuenta": 1006,
            "saldo_inicial": 450000,
            "tipo": " AHORRO ",
            "tasa_interes": "texto",
        },
        {
            "titular": "maría josé gallardo",
            "numero_cuenta": 1007,
            "saldo_inicial": 600000,
            "tipo": "CORRIENTE",
            "limite_giro": "error",
        },
        {
            "titular": "Felipe Mansilla",
            "numero_cuenta": 1008,
            "saldo_inicial": 250000,
            "tipo": "corriente",
            "limite_giro": -50000,
        },
        {
            "titular": "Fernanda Díaz",
            "numero_cuenta": 1009,
            "saldo_inicial": 900000,
            "tipo": "ahorro",
            "tasa_interes": -1.5,
        },
        {
            "titular": "Rodrigo Vera",
            "numero_cuenta": 1010,
            "saldo_inicial": 150000,
            "tipo": "corriente",
            "limite_giro": 300000,
        },
        {
            "titular": "Claudio Bravo",
            "numero_cuenta": 1001,
            "saldo_inicial": 10000,
            "tipo": "ahorro",
        },
        {
            "numero_cuenta": 1011,
            "saldo_inicial": 50000,
            "tipo": "ahorro",
        },
        {
            "titular": "Lorena Cárcamo",
            "saldo_inicial": 75000,
            "tipo": "corriente",
        },
        {
            "titular": "Álvaro Cárcamo",
            "numero_cuenta": 1012,
            "tipo": "ahorro",
        },
        {
            "titular": "Beatriz Vera",
            "numero_cuenta": 1013,
            "saldo_inicial": 40000,
        },
        {
            "titular": "Gonzalo Muñoz",
            "numero_cuenta": "letras",
            "saldo_inicial": 20000,
            "tipo": "ahorro",
        },
        {
            "titular": "Esteban Paredes",
            "numero_cuenta": 1014,
            "saldo_inicial": -100,
            "tipo": "corriente",
        },
        {
            "titular": "Arturo Vidal",
            "numero_cuenta": 1015,
            "saldo_inicial": "veinte",
            "tipo": "ahorro",
        },
        {
            "titular": "Alexis Sánchez",
            "numero_cuenta": 1016,
            "saldo_inicial": 500000,
            "tipo": "inversion",
        },
        {
            "titular": "   ",
            "numero_cuenta": 1017,
            "saldo_inicial": 30000,
            "tipo": "ahorro",
        },
        {
            "titular": "Jorge Valdivia",
            "numero_cuenta": 1002,
            "saldo_inicial": 45000,
            "tipo": "corriente",
        },
        {
            "titular": None,
            "numero_cuenta": 1018,
            "saldo_inicial": 50000,
            "tipo": "ahorro",
        },
    ]

    print(f"total registros antes {len(datos_brutos)}")
    cuentas_limpias = preprocesar_cuentas(datos_brutos)
    print(f"total cuentas validas {len(cuentas_limpias)}")

    for c in cuentas_limpias:
        print(c)

    print("iniciando banco")

    banco = Banco("Banco Magallanes")
    print(f"banco creado {banco.nombre}")

    for c in cuentas_limpias:
        if c["tipo"] == "ahorro":
            nueva_cuenta = CuentaDeAhorro(
                titular=c["titular"],
                numero_cuenta=c["numero_cuenta"],
                tasa_interes=c["tasa_interes"],
            )
        else:
            nueva_cuenta = CuentaCorriente(
                titular=c["titular"],
                numero_cuenta=c["numero_cuenta"],
                limite_giro=c["limite_giro"],
            )

        if c["saldo_inicial"] > 0:
            nueva_cuenta.depositar(c["saldo_inicial"])

        banco.abrir_cuenta(nueva_cuenta)

    banco.mostrar_cuentas()

    c_ahorro = banco.buscar_cuenta(1001)
    c_corriente = banco.buscar_cuenta(1002)

    if c_ahorro and c_corriente:
        print("prueba deposito y giro")
        print(f"saldo cuenta 1001 {c_ahorro.consultar_saldo()}")
        c_ahorro.depositar(50000)
        print(f"saldo despues de meter plata {c_ahorro.consultar_saldo()}")

        print(f"saldo cuenta 1002 {c_corriente.consultar_saldo()}")
        c_corriente.girar(100000)
        print(f"saldo despues de sacar plata {c_corriente.consultar_saldo()}")

    print("prueba sobregiro")
    if isinstance(c_corriente, CuentaCorriente):
        print(
            f"saldo antes de sobregiro {c_corriente.consultar_saldo()} limite {c_corriente.limite_giro}"
        )
        c_corriente.girar(300000)
        print(
            f"saldo con sobregiro {c_corriente.consultar_saldo()}"
        )

        try:
            c_corriente.girar(200000)
        except ValueError as error:
            print(f"error esperado capturado {error}")

    print("prueba de giro sin plata en ahorro")
    if c_ahorro:
        try:
            c_ahorro.girar(9999999)
        except ValueError as error:
            print(f"error capturado {error}")

    print("aplicando interes")
    if isinstance(c_ahorro, CuentaDeAhorro):
        print(
            f"saldo ahorro {c_ahorro.consultar_saldo()} tasa {c_ahorro.tasa_interes}"
        )
        ganancia = c_ahorro.aplicar_interes()
        print(
            f"interes agregado {ganancia} saldo nuevo {c_ahorro.consultar_saldo()}"
        )

    print("prueba transferir")
    c_destino = banco.buscar_cuenta(1004)
    if c_ahorro and c_destino:
        print(
            f"antes origen {c_ahorro.consultar_saldo()} destino {c_destino.consultar_saldo()}"
        )
        banco.transferir(1001, 1004, 150000)
        print("transferencia hecha")
        print(
            f"despues origen {c_ahorro.consultar_saldo()} destino {c_destino.consultar_saldo()}"
        )

    print("cuentas finales")
    banco.mostrar_cuentas()


if __name__ == "__main__":
    main()