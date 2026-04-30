import asyncio
import ssl
import struct
from dnslib import DNSRecord, QTYPE, RR, A, AAAA, DNSHeader
import requests
import logging

logger = logging.getLogger(__name__)

class DNSOverTLSHandler:
    def __init__(self, resolver):
        self.resolver = resolver
    
    async def handle(self, reader, writer):
        try:
            data = await reader.read(1024)
            if not data:
                return
            
            # DoT uses 2-byte length prefix
            if len(data) > 2:
                dns_msg = data[2:] if len(data) > 2 else data
            else:
                dns_msg = data
            
            response = await self.resolver.resolve(dns_msg, 'dot')
            
            # Add length prefix for DoT response
            length = struct.pack('!H', len(response))
            writer.write(length + response)
            await writer.drain()
        except Exception as e:
            logger.error(f"DoT error: {e}")
        finally:
            writer.close()
            await writer.wait_closed()

class DNSOverHTTPSHandler:
    def __init__(self, resolver):
        self.resolver = resolver
    
    async def handle_get(self, request):
        from flask import request as flask_request
        dns_b64 = flask_request.args.get('dns', '')
        padding = 4 - len(dns_b64) % 4
        if padding != 4:
            dns_b64 += '=' * padding
        import base64
        dns_msg = base64.urlsafe_b64decode(dns_b64)
        return await self.resolver.resolve(dns_msg, 'doh')
    
    async def handle_post(self, request):
        from flask import request as flask_request
        dns_msg = flask_request.get_data()
        return await self.resolver.resolve(dns_msg, 'doh')

async def start_dot_server(resolver, port=853):
    handler = DNSOverTLSHandler(resolver)
    server = await asyncio.start_server(handler.handle, '0.0.0.0', port)
    logger.info(f"DoT server started on port {port}")
    async with server:
        await server.serve_forever()

def start_dns_servers():
    from core.resolver import SmartResolver
    resolver = SmartResolver()
    
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    # Start DoT server
    loop.run_until_complete(start_dot_server(resolver, 853))
