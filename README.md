# Mikrotik new versions checker

## Mikrotik script

```
:local clientID "your-random-unique-id";
:local mailEmail "your email";
:local mailSubject "New version of mikrotik's firmware has been released.";
:local filename "new-version.txt";

/tool fetch url="http://mikrotik-version.herokuapp.com/check/$clientID"
mode=http dst-path=$filename;
:local result [/file get $filename contents];
if ($result != "") do={
  /tool e-mail send subject=$mailSubject to=$mailEmail file=$filename;

}
```

Important: [/tool e-mail](http://wiki.mikrotik.com/wiki/Manual:Tools/email)
must be configured.
