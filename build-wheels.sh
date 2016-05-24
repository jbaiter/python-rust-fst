#!/bin/bash
set -e -x

OPENSSL_VERSION=1.0.2h
CURL_VERSION=7.49.0
RUST_CHANNEL=nightly

# Remove old wheels
rm -rf /io/wheelhouse/* || echo "No old wheels to delete"

# We don't support Python 2.6
rm -rf /opt/python/cp26*

# Override PATH and LD_LIBRARY so that our curl and openssl installations
# get precedence over the included versions
PATH=/opt/curl/bin:$PATH
LD_LIBRARY_PATH=/opt/openssl/lib:$LD_LIBRARY_PATH

# Install libraries needed for compiling the extension
yum -y install libffi-devel

# Update the Root CA bundle
wget --no-check-certificate \
    -O /etc/pki/tls/certs/ca-bundle.crt \
    http://curl.haxx.se/ca/cacert.pem

# Compile and parallel-install a newer OpenSSL version so that curl can
# download from the rust servers
# Note that we cannot download from the official OpenSSL servers, since they
# require HTTPS, which does not work with the CentOS5 SSL version...
cd /usr/src
wget http://ftp.vim.org/security/openssl/openssl-${OPENSSL_VERSION}.tar.gz
tar xf openssl-${OPENSSL_VERSION}.tar.gz
cd openssl-${OPENSSL_VERSION}
./config --prefix=/opt/openssl shared
make
make install
cd ..

# Compile an up-to-date curl version that links to our own OpenSSL installation
wget --no-check-certificate http://curl.haxx.se/download/curl-${CURL_VERSION}.tar.gz
tar xf curl-${CURL_VERSION}.tar.gz
cd curl-${CURL_VERSION}
./configure --with-ssl=/opt/openssl --prefix=/opt/curl
make
make install
cd $HOME

# Install rust
curl https://static.rust-lang.org/rustup.sh > /tmp/rustup.sh
chmod +x /tmp/rustup.sh
/tmp/rustup.sh -y --disable-sudo --channel=$RUST_CHANNEL

# Compile wheels
for PYBIN in /opt/python/*/bin; do
    ${PYBIN}/pip install pytest
    ${PYBIN}/pip wheel /io/ -w wheelhouse/
done

# Move pure wheels to output wheelhouse
mkdir -p /io/wheelhouse/
mv wheelhouse/*any.whl /io/wheelhouse/ || echo "No pure wheels found."

# Bundle external shared libraries into the wheels
for whl in wheelhouse/*.whl; do
    auditwheel repair $whl -w /io/wheelhouse/
done

# Set permissions on wheels
chmod -R a+rw /io/wheelhouse

# Install packages and test
for PYBIN in /opt/python/*/bin/; do
    ${PYBIN}/pip install rust_fst --no-index -f /io/wheelhouse
    ${PYBIN}/py.test --verbose /io/tests
    rm -f /io/rust_fst/_ffi.py
    find /io -name "__pycache__" -type d -print0 |xargs rm -rf --
    find /io -name "*.pyc" -type f -print0 |xargs rm -rf --
done
