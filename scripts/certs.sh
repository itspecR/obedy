#!/usr/bin/env bash

CA_DIR=/etc/obedy/ca
CA_KEY="$CA_DIR/ca.key"
CA_CERT="$CA_DIR/ca.pem"
CA_DOMAIN_FILE="$CA_DIR/domain"
ISSUED_DIR="$CA_DIR/issued"
CA_DAYS=3650
LEAF_DAYS=825
CA_KEY_BITS=3072
LEAF_KEY_BITS=2048
PRIVATE_IP_SUBTREES="IP:10.0.0.0/255.0.0.0,permitted;IP:172.16.0.0/255.240.0.0,permitted;IP:192.168.0.0/255.255.0.0"
DOMAIN_PATTERN='^([a-z0-9]([a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z0-9]([a-z0-9-]{0,61}[a-z0-9])?$'
IPV4_PATTERN='^[0-9]{1,3}(\.[0-9]{1,3}){3}$'
PRIVATE_IPV4_PATTERN='^(10\.|192\.168\.|172\.(1[6-9]|2[0-9]|3[01])\.)'

ca_exists() {
    [[ -s "$CA_KEY" && -s "$CA_CERT" && -s "$CA_DOMAIN_FILE" ]]
}

ca_domain() {
    cat "$CA_DOMAIN_FILE"
}

valid_domain() {
    [[ "$1" =~ $DOMAIN_PATTERN ]]
}

in_domain() {
    [[ "$1" == "$2" || "$1" == *".$2" ]]
}

is_private_ipv4() {
    [[ "$1" =~ $IPV4_PATTERN && "$1" =~ $PRIVATE_IPV4_PATTERN ]]
}

private_ipv4_addresses() {
    local ip
    for ip in $(hostname -I); do
        if is_private_ipv4 "$ip"; then echo "$ip"; fi
    done
}

ca_config() {
    cat <<EOF
[req]
distinguished_name = subject
x509_extensions = authority
prompt = no
[subject]
O = Obedy
CN = Obedy CA $1
[authority]
basicConstraints = critical,CA:TRUE,pathlen:0
keyUsage = critical,keyCertSign,cRLSign
subjectKeyIdentifier = hash
nameConstraints = critical,permitted;DNS:$1,permitted;$PRIVATE_IP_SUBTREES
EOF
}

leaf_extensions() {
    printf '%s\n' \
        "basicConstraints=critical,CA:FALSE" \
        "keyUsage=critical,digitalSignature,keyEncipherment" \
        "extendedKeyUsage=serverAuth" \
        "subjectKeyIdentifier=hash" \
        "authorityKeyIdentifier=keyid" \
        "subjectAltName=$1"
}

create_ca() {
    mkdir -p "$ISSUED_DIR"
    chmod 700 "$CA_DIR" "$ISSUED_DIR"
    openssl req -x509 -new -newkey "rsa:$CA_KEY_BITS" -nodes -days "$CA_DAYS" \
        -config <(ca_config "$1") -keyout "$CA_KEY" -out "$CA_CERT" 2>/dev/null \
        || fail "Не удалось создать центр сертификации"
    chmod 600 "$CA_KEY"
    echo "$1" > "$CA_DOMAIN_FILE"
}

issue_cert() {
    local name="$1" san="$2" key="$3" cert="$4" request
    request="$(mktemp)"
    openssl req -new -newkey "rsa:$LEAF_KEY_BITS" -nodes -subj "/CN=$name" -keyout "$key" -out "$request" 2>/dev/null \
        || fail "Не удалось создать ключ для $name"
    openssl x509 -req -in "$request" -CA "$CA_CERT" -CAkey "$CA_KEY" -set_serial "0x$(openssl rand -hex 16)" \
        -days "$LEAF_DAYS" -extfile <(leaf_extensions "$san") -out "$cert" 2>/dev/null \
        || fail "Не удалось выпустить сертификат для $name"
    rm -f "$request"
    chmod 600 "$key"
}
