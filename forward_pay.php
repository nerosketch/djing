#!/usr/bin/env php
<?php

define("API_AUTH_SECRET", "secret");
define("SERVER_DOMAIN", 'http://localhost:8000');
define('N', '
');


function calc_hash($str)
{
    $hash = bin2hex(mhash(MHASH_SHA256,$str));
    return $hash;
}


function make_sign($data)
{
    asort($data, SORT_STRING);
    array_push($data, API_AUTH_SECRET);
    $str_to_hash = join('_', $data);
    return calc_hash($str_to_hash);
}


function send_to($data)
{
    $sign = make_sign($data);
    $data['sign'] = $sign;
    $url_params = http_build_query($data);
    $r = file_get_contents(SERVER_DOMAIN."/abons/api/duplicate_pay/?".$url_params);
    return $r;
}



function forward_pay_request($act, $pay_account, $service_id, $trade_point, $receipt_num, $pay_id, $pay_amount)
{
    require('./users_uname_pk_pairs.php');

    // $user_id_pairs

    if($act == 1)
    {
        $pay = [
            "ACT" => 1,
            "PAY_ACCOUNT" => $user_id_pairs[$pay_account]
        ];
        return send_to($pay);
    }else if($act == 4)
    {
        $pay = [
            "ACT" => 4,
            "PAY_ACCOUNT" => $user_id_pairs[$pay_account],
            "TRADE_POINT" => $trade_point,
            "RECEIPT_NUM" => $receipt_num,
            "PAY_ID" => $pay_id,
            "PAY_AMOUNT" => $pay_amount,
            "SERVICE_ID" => $service_id
        ];
        return send_to($pay);
    }else if($act == 7)
    {
        $pay = [
            "ACT" => 7,
            "PAY_ID" => $pay_id,
            "SERVICE_ID" => $service_id
        ];
        return send_to($pay);
    }

}

# Request
echo forward_pay_request(1, '1234', null, null, null, null, null);

# Add cash
echo forward_pay_request('4', '1234', 'mypaysrv', '3432', '289473', '897879-989-68669', '1');

# check cash
echo forward_pay_request(7, null, 'mypaysrv', null, null, '897879-989-68669', null);

?>
