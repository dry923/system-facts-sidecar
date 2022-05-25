FROM registry.access.redhat.com/ubi8:latest

RUN dnf install -y --nodocs python3 python3-pip jq && dnf clean all
RUN pip3 install --upgrade pip
COPY requirements.txt requirements.txt
RUN pip3 install -r requirements.txt
RUN curl -sS https://mirror.openshift.com/pub/openshift-v4/x86_64/clients/ocp/latest/openshift-client-linux.tar.gz | tar xz -C /usr/bin/
RUN chmod +x /usr/bin/oc /usr/bin/kubectl
COPY gather_facts.py gather_facts.py
